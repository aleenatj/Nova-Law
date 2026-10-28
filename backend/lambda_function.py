import base64
import os, json, psycopg2
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 10

import logging
logger = logging.getLogger(__name__)

# Setup Postgres connection (use RDS Proxy for Lambda in production!)
def get_conn():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASS"],
        port=os.environ.get("PG_PORT", 5432)
    )

apigw = boto3.client(
    "apigatewaymanagementapi",
    endpoint_url=os.environ["WEBSOCKET_ENDPOINT"]
)

def lambda_handler(event, context):
    route = event["requestContext"]["routeKey"]
    if route == "$connect":
        conn_id = event["requestContext"]["connectionId"]
        return handle_connect(event, conn_id)
    elif route == "$disconnect":
        conn_id = event["requestContext"]["connectionId"]
        return handle_disconnect(conn_id)
    elif route == "sendMessage":
        body = event["body"]
        if body:
            body_json = json.loads(body)
            if "messages" in body_json:
                messages = body_json["messages"]
                return handle_send_message(messages)
            else:
                return {"statusCode": 200, "body": "No messages"}
        else:
            return {"statusCode": 200, "body": "No body"}
    elif route == "$default":
        conn_id = event["requestContext"]["connectionId"]
        # return handle_default(event, conn_id)
    else:
        return {"statusCode": 200, "body": "Unhandled route"}

def extract_and_verify_auth_token(event: dict) -> tuple[str, str] | dict[str, object]:
    """
    Extract the authentication token from the event and verify it using the FastAPI /verify-token endpoint.

    Args:
        event: The Lambda event dictionary.

    Returns:
        Tuple of (user_id, role_code) if successful, or a response dict if authentication fails.
    """
    auth_token: str | None = None

    # Try to get token from queryStringParameters
    query_params: dict = event.get("queryStringParameters") or {}
    auth_token = query_params.get("auth_token")

    if not auth_token:
        logger.warning("Missing authentication token in connection request")
        return {"statusCode": 401, "body": "Missing authentication token"}

    VERIFY_TOKEN_URL: str | None = os.environ.get("VERIFY_TOKEN_URL")
    if not VERIFY_TOKEN_URL:
        logger.error("VERIFY_TOKEN_URL environment variable not set")
        return {"statusCode": 500, "body": "Server configuration error"}

    resp_json: dict = {}
    try:
        # Build the URL with the token as a query parameter
        from urllib.parse import urlencode

        query_string = urlencode({"token": auth_token})
        verify_url = f"{VERIFY_TOKEN_URL}?{query_string}"
        api_key = os.environ.get("WEBSOCKET_API_KEY")
        if not api_key:
            logger.error("WEBSOCKET_API_KEY environment variable not set")
            return {"statusCode": 500, "body": "Server configuration error"}

        event = {
            "version": "2.0",
            "routeKey": "POST /api/v1/auth/verify-token",
            "rawPath": "/api/v1/auth/verify-token",
            "rawQueryString": f"token={auth_token}",
            "headers": {
                "content-type": "application/json",
                "x-api-key": api_key
            },
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/api/v1/auth/verify-token",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "lambda-invoke"
                }
            },
            "body": None,
            "isBase64Encoded": False
        }

        client = boto3.client("lambda")
        response = client.invoke(
            FunctionName="nova-law-api",
            InvocationType="RequestResponse",
            Payload=json.dumps(event),
        )

        response = json.loads(response["Payload"].read())   
        resp_json = json.loads(response.get('body', {}))
        if not resp_json.get("success"):
            logger.warning(f"Token verification unsuccessful: {resp_json.get('message')}")
            return {"statusCode": 401, "body": "Authentication failed"}
    except Exception as e:
        logger.error(f"Error calling verify-token endpoint: {e}")
        return {"statusCode": 500, "body": "Authentication service error"}

    # Extract user info from verification response
    user_data: dict = resp_json.get("data", {})
    user_id: str | None = user_data.get("user_id")
    role_code: str | None = user_data.get("role_code")
    
    def decode_id(encrypted_id: str) -> str | None:
        try:
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            import hashlib
            def get_key(secret_key: str | None = None):    
                """
                Derive a deterministic IV (Initialization Vector) from the salt for use in AES modes that require an IV.
                This uses the salt (or a default from settings) and the secret key to derive a 16-byte IV using SHA-256.
                """
                try:
                    if secret_key and isinstance(secret_key, str):
                        source = (secret_key).encode("utf-8")
                    else:
                        source = (secret_key.decode("utf-8")).encode("utf-8")
                    key = hashlib.sha256(source).digest()
                    iv = hashlib.sha256(source).digest()[:16]
                    
                    return key, iv
                except Exception as e:
                    logger.error(f"Error getting key: {e}")
                    return None, None            
            backend = default_backend()
            secret_key = os.environ.get("WEBSOCKET_TOKEN_ENCRYPTION_KEY") or datetime.now().strftime("%Y%m%d%H")
            key, iv = get_key(secret_key)    
            encrypted_data = bytes.fromhex(encrypted_id)

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
            
            if decrypted_data.decode('utf-8') == "None":
                return None
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting id: {e}")
            return None    
    
    if user_id:
        user_id = decode_id(user_id)
    if not user_id or not role_code:
        logger.error("User ID missing in token verification response")
        return {"statusCode": 401, "body": "Invalid authentication token"}
    return user_id, role_code
    
def handle_connect(event, conn_id):

    # Use the new function in handle_connect
    result = extract_and_verify_auth_token(event)
    if isinstance(result, dict):
        return result
    user_id, role_code = result  # you can also extract from auth token
    if not user_id:
        return {"statusCode": 401, "body": "Missing user_id"}
    if not role_code:
        return {"statusCode": 401, "body": "Missing role_code"}

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO websocket_connections (user_id, connection_id, connected_at, created_at, updated_at, role_code)
            VALUES (%s, %s, %s, now(), now(), %s)
            ON CONFLICT (user_id, connection_id) DO UPDATE
            SET connected_at = EXCLUDED.connected_at, updated_at = now()
        """, (user_id, conn_id, datetime.now(timezone.utc), role_code))
        conn.commit()

    return {"statusCode": 200}

def handle_disconnect(conn_id):
    """
    Handles disconnection by marking the connection as disconnected and
    additionally deletes up to 10 old connections disconnected more than 2 days ago.
    """
    with get_conn() as conn, conn.cursor() as cur:
        # Update current connection as disconnected
        cur.execute(
            """
            UPDATE websocket_connections
            SET disconnected_at = now(), updated_at = now()
            WHERE connection_id = %s
            """,
            (conn_id,),
        )
        # Delete up to 10 connections that have been disconnected for more than 2 days
        cur.execute(
            """
                DELETE FROM websocket_connections
                WHERE (user_id, connection_id) IN (
                SELECT user_id, connection_id
                FROM websocket_connections
                WHERE disconnected_at IS NOT NULL
                    AND disconnected_at < (now() - INTERVAL '2 days')
                LIMIT 10
                );
            """
        )
        conn.commit()
    return {"statusCode": 200}


def _send_single(message):
    """Helper: send a single message to a connection."""
    connection_id = message.get("connection_id")
    msg = message.get("message")

    if not (msg and connection_id):
        logger.error("No connection_id or msg")
        return (connection_id, False, None, "Invalid message")

    try:
        if isinstance(msg, dict):
            msg = json.dumps(msg).encode("utf-8")
        else:
            msg = str(msg).encode("utf-8")
        apigw.post_to_connection(ConnectionId=connection_id, Data=msg)
        return (connection_id, True, None, None)

    except ClientError as e:
        if e.response["Error"]["Code"] == "GoneException":
            # Mark stale connection for batch cleanup
            logger.info("Stale connection: %s", connection_id)
            return (connection_id, False, True, None)
        else:
            logger.error("ClientError for %s: %s", connection_id, str(e))
            return (connection_id, False, None, str(e))
    except Exception as e:
        logger.error("Unexpected error for %s: %s", connection_id, str(e))
        return (connection_id, False, None, str(e))


def handle_send_message(messages):
    """
    Send messages to WebSocket connections.
    
    Messages are grouped by connection_id and processed sequentially per connection
    to ensure proper ordering. Different connections are processed in parallel for performance.
    
    This ensures:
    - Messages to the same connection arrive in order (FIFO)
    - No overlapping messages to the same connection
    - Different connections can still be processed in parallel
    """
    try:
        results = []
        stale_ids = []
        
        # Group messages by connection_id to ensure ordering per connection
        messages_by_connection = {}
        for msg in messages:
            connection_id = msg.get("connection_id")
            if connection_id:
                if connection_id not in messages_by_connection:
                    messages_by_connection[connection_id] = []
                messages_by_connection[connection_id].append(msg)
        
        def _send_connection_messages(connection_id, connection_messages):
            """
            Send all messages for a single connection sequentially.
            This ensures messages to the same connection are sent in order.
            """
            connection_results = []
            for msg in connection_messages:
                connection_id_result, ok, stale, err = _send_single(msg)
                connection_results.append((connection_id_result, ok, stale, err))
                if stale:
                    return connection_results, True  # Return early if connection is stale
            return connection_results, False
        
        # Process each connection's messages sequentially, but different connections in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_connection = {
                executor.submit(_send_connection_messages, conn_id, msgs): conn_id
                for conn_id, msgs in messages_by_connection.items()
            }
            
            for future in as_completed(future_to_connection):
                connection_results, is_stale = future.result()
                results.extend(connection_results)
                if is_stale:
                    connection_id = future_to_connection[future]
                    stale_ids.append(connection_id)

        sent = sum(1 for _, ok, _, _ in results if ok)
        failed = len(results) - sent

        # Batch delete stale connections
        if stale_ids:
            try:
                with get_conn() as conn, conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM websocket_connections WHERE connection_id = ANY(%s)",
                        (stale_ids,)
                    )
                    conn.commit()
                logger.info("Batch removed %d stale connections", len(stale_ids))
            except Exception as e:
                logger.error("Error cleaning up stale connections: %s", str(e))

        logger.info("Sent: %d, Failed: %d (processed %d connections)", sent, failed, len(messages_by_connection))

        return {"statusCode": 200, "body": f"Sent {sent}, failed {failed}"}

    except Exception as e:
        logger.error("Error in send message: %s", str(e))
        return {"statusCode": 500, "body": "Error sending messages"}