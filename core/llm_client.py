import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .logger import setup_logger

load_dotenv()
logger = setup_logger("LLM")

# Module-level singletons (mirrors TypeScript module-level `client` and `cachedSecret`)
_client: genai.Client | None = None
_cached_aws_secret: dict | None = None


# ---------------------------------------------------------------------------
# AWS Secrets Manager helper (production path)
# ---------------------------------------------------------------------------

def _load_vertex_key_from_secrets_manager() -> tuple[str, dict]:
    """Load the Vertex AI service-account key from AWS Secrets Manager.

    The secret is expected to be a JSON object whose key equals the secret name
    (e.g. ``{"thrilia/google/vertex/service-account": "<SA-JSON-string>"}``)
    — matching the TypeScript convention exactly.

    Returns:
        (key_string, parsed_key) — the raw SA JSON string and the parsed dict.
    """
    global _cached_aws_secret

    if _cached_aws_secret:
        logger.info("[load_vertex_key] Using cached secret")
        return _cached_aws_secret

    logger.info("[load_vertex_key] Loading from AWS Secrets Manager")

    secret_name = os.getenv("VERTEX_SECRET_ID")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not secret_name:
        raise ValueError("VERTEX_SECRET_ID env var is required in vertex/production mode")

    try:
        import boto3
    except ImportError as exc:
        raise ImportError(
            "boto3 is required for production (vertex) mode. "
            "Run: poetry add boto3"
        ) from exc

    sm_client = boto3.client("secretsmanager", region_name=region)
    response = sm_client.get_secret_value(SecretId=secret_name)

    if not response.get("SecretString"):
        raise ValueError("No SecretString found in AWS Secrets Manager response")

    try:
        outer = json.loads(response["SecretString"])
    except json.JSONDecodeError as exc:
        raise ValueError("Failed to parse SecretString as JSON") from exc

    # The TS code does: key['thrilia/google/vertex/service-account']
    # i.e. the outer JSON has the secret name as a key.
    key_string: str = outer.get(secret_name, response["SecretString"])
    if not isinstance(key_string, str):
        key_string = json.dumps(key_string)

    try:
        parsed_key: dict = json.loads(key_string)
    except json.JSONDecodeError as exc:
        raise ValueError("Failed to parse service-account key JSON from secret") from exc

    logger.info("[load_vertex_key] Secret loaded and parsed successfully")
    _cached_aws_secret = (key_string, parsed_key)
    return _cached_aws_secret


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def _create_gemini_client() -> genai.Client:
    """Create (and cache) a Gemini client.

    Mirrors ``createGeminiClient()`` from the TypeScript codebase:

    - ``USE_GENAI_MODE=studio``  → Studio mode, uses GEMINI_API_KEY
    - ``USE_GENAI_MODE=vertex``  → Vertex AI mode
        - ``NODE_ENV=development`` → reads a local service-account JSON file
          (path from VERTEX_SA_PATH or ``core/thrilia-vertex-sa.json``)
        - ``NODE_ENV=production``  → fetches key from AWS Secrets Manager
    """
    global _client
    if _client:
        return _client

    mode = os.getenv("USE_GENAI_MODE", "studio").lower()

    # ------------------------------------------------------------------
    # STUDIO mode
    # ------------------------------------------------------------------
    if mode == "studio":
        logger.info("[create_gemini_client] Creating client in STUDIO mode with API key")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY env var is required in studio mode")
        _client = genai.Client(api_key=api_key)
        return _client

    # ------------------------------------------------------------------
    # VERTEX mode
    # ------------------------------------------------------------------
    logger.info("[create_gemini_client] Creating client in VERTEX mode")

    node_env = os.getenv("NODE_ENV", "production").lower()
    parsed_key: dict = {}

    if node_env == "development":
        # ---- LOCAL DEV PATH (no AWS, use JSON file) ----
        key_path = os.getenv("VERTEX_SA_PATH") or str(
            Path(__file__).parent / "thrilia-vertex-sa.json"
        )
        logger.info(f"[create_gemini_client] Using local service account JSON: {key_path}")

        with open(key_path, "r", encoding="utf-8") as fh:
            parsed_key = json.load(fh)

        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
            logger.info(
                f"[create_gemini_client] GOOGLE_APPLICATION_CREDENTIALS set to {key_path}"
            )

    else:
        # ---- PROD PATH (load from AWS Secrets Manager) ----
        logger.info("[create_gemini_client] Loading Vertex key from AWS Secrets Manager")
        key_string, parsed_key = _load_vertex_key_from_secrets_manager()

        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            cred_path = "/tmp/vertex-sa.json"
            with open(cred_path, "w", encoding="utf-8") as fh:
                fh.write(key_string)
            os.chmod(cred_path, 0o600)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
            logger.info(
                f"[create_gemini_client] GOOGLE_APPLICATION_CREDENTIALS set to {cred_path}"
            )

    project = os.getenv("VERTEX_PROJECT_ID") or parsed_key.get("project_id")
    location = os.getenv("VERTEX_LOCATION", "us-central1")

    _client = genai.Client(
        vertexai=True,
        project=project,
        location=location,
    )
    logger.info("[create_gemini_client] Gemini client (vertex) created")
    return _client


# ---------------------------------------------------------------------------
# LLMClient — same public interface as before
# ---------------------------------------------------------------------------

class LLMClient:
    def __init__(self):
        self.client = _create_gemini_client()
        self.model_name = os.getenv("VERTEX_MODEL_NAME", "gemini-1.5-pro")
        logger.info(f"LLMClient initialized with model: {self.model_name}")

    def query(self, system_prompt: str, user_prompt: str, response_format: str = "text"):
        """Query the Gemini model and return the response.

        Args:
            system_prompt: System-level instruction for the model.
            user_prompt: The user-facing prompt / task description.
            response_format: ``"json"`` to parse the response as JSON,
                             ``"text"`` (default) to return raw text.

        Returns:
            Parsed dict (JSON mode) or string (text mode), or ``None`` on error.
        """
        logger.info(f"Sending query to Gemini (format={response_format})")

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type=(
                    "application/json" if response_format == "json" else "text/plain"
                ),
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                config=config,
                contents=user_prompt,
            )

            content: str = response.text
            return json.loads(content) if response_format == "json" else content

        except Exception as exc:
            err = str(exc)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                logger.error(
                    "🛑 QUOTA EXCEEDED (429): You have hit your Gemini API rate limits."
                )
            else:
                logger.error(f"Gemini API Error: {err}")
            return None
