import json
import gzip
import boto3
from datetime import datetime
from urllib.parse import unquote_plus

s3 = boto3.client("s3")
cw = boto3.client("cloudwatch")

REQUIRED_FIELDS = {
    "page_view":    ["user_id", "session_id", "page_url", "page_type",
                     "timestamp", "time_on_page_seconds", "device_type", "country"],
    "click":        ["user_id", "session_id", "element_id", "element_type",
                     "page_url", "timestamp", "x_position", "y_position"],
    "search":       ["user_id", "session_id", "query", "results_count", "timestamp"],
    "product_view": ["user_id", "session_id", "product_id", "category",
                     "price", "timestamp", "time_on_page_seconds"],
    "cart_event":   ["user_id", "session_id", "product_id", "action", "timestamp"],
}


def validate_record(rec):
    etype = rec.get("event_type")
    if etype not in REQUIRED_FIELDS:
        return False, f"event_type desconocido: {etype}"
    for field in REQUIRED_FIELDS[etype]:
        if field not in rec or rec[field] is None:
            return False, f"campo obligatorio ausente: {field}"
    try:
        datetime.fromisoformat(rec["timestamp"])
    except Exception:
        return False, "timestamp invalido"
    return True, "ok"


def put_metric(name, value, unit="Count"):
    try:
        cw.put_metric_data(
            Namespace="ShopStream/Ingesta",
            MetricData=[{"MetricName": name, "Value": value, "Unit": unit}]
        )
    except Exception as e:
        print(f"Warning CloudWatch: {e}")


def lambda_handler(event, context):
    for rec in event["Records"]:
        bucket = rec["s3"]["bucket"]["name"]
        key    = unquote_plus(rec["s3"]["object"]["key"])
        size   = rec["s3"]["object"]["size"]

        print(f"Procesando: s3://{bucket}/{key}")

        # Descargar objeto
        obj  = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read()
        if key.endswith(".gz"):
            body = gzip.decompress(body)

        # Procesar línea por línea sin guardar todo en memoria
        valid_count   = 0
        invalid_count = 0
        invalid_sample = []  # solo guardamos muestra de 100 invalidos

        for line in body.decode("utf-8").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                ok, msg = validate_record(r)
                if ok:
                    valid_count += 1
                else:
                    invalid_count += 1
                    if len(invalid_sample) < 100:
                        invalid_sample.append({"record": r, "error": msg})
            except json.JSONDecodeError as e:
                invalid_count += 1
                if len(invalid_sample) < 100:
                    invalid_sample.append({"raw": line[:200], "error": str(e)})

        # Liberar memoria
        del body

        # Métricas CloudWatch
        put_metric("ArchivosProcessados", 1)
        put_metric("RegistrosValidos",    valid_count)
        put_metric("RegistrosInvalidos",  invalid_count)
        put_metric("TamanioBytes",        size, "Bytes")

        # Guardar muestra de inválidos en quarantine/
        if invalid_sample:
            qkey    = key.replace("raw/", "quarantine/", 1) + ".errors.json"
            meta    = {"error_count": invalid_count, "source_key": key,
                       "processed_at": datetime.utcnow().isoformat()}
            payload = json.dumps({"metadata": meta, "invalid_records": invalid_sample})
            s3.put_object(Bucket=bucket, Key=qkey, Body=payload.encode("utf-8"))
            print(f"Invalidos guardados en: {qkey}")

        print(f"Resultado: {valid_count:,} validos, {invalid_count:,} invalidos")

    return {"statusCode": 200}
