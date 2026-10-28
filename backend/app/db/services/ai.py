"""AI service functions for AI-powered features."""

from typing import Any
import yaml

from app.agents.llm import LLMAgent
from app.core.config import settings
from app.core.logging import get_logger
from app.enums.case import CaseTypeEnum
from app.db.services.general import get_prompt_template_path
from app.db.models.case import Case

logger = get_logger(__name__)


def load_yaml_prompt_template(template_path: str) -> dict[str, Any]:
    """
    Load YAML prompt template from file.

    Args:
        template_path: Path to the YAML template file

    Returns:
        Dictionary containing the prompt template configuration

    Raises:
        FileNotFoundError: If template file doesn't exist
        yaml.YAMLError: If template file is invalid YAML
    """
    try:
        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)
        
        if not template:
            raise ValueError(f"Empty YAML template at {template_path}")

        return template

    except Exception as e:
        logger.exception(f"Error loading YAML template: {e}")
        raise


def fill_prompt_placeholders(template: str, data: dict[str, Any]) -> str:
    """
    Fill placeholders in prompt template with actual data.

    Args:
        template: Template string with placeholders like {placeholder_name}
        data: Dictionary with values to replace placeholders

    Returns:
        String with placeholders replaced by actual values
    """
    try:
        # Replace placeholders with actual values
        filled_template = template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            # Convert value to string, handling None values
            str_value = str(value) if value is not None else ""
            filled_template = filled_template.replace(placeholder, str_value)
        
        return filled_template
    
    except Exception as e:
        logger.exception(f"Error filling prompt placeholders: {e}")
        raise


def format_case_details_for_prompt(case_summary: dict) -> str:
    """
    Format case summary data into a readable string for the prompt.

    Args:
        case_summary: Dictionary containing case summary with Q&A pairs

    Returns:
        Formatted string of case details
    """
    try:
        summary_items = case_summary.get("summary", [])
        
        if not summary_items:
            return "No case details available."
        
        formatted_lines = []
        for item in summary_items:
            question = item.get("question", "")
            answer = item.get("answer", "")
            
            # Handle answer which can be string or list
            if isinstance(answer, list):
                answer_str = ", ".join(str(a) for a in answer if a)
            else:
                answer_str = str(answer) if answer else "Not provided"
            
            if question and answer_str:
                formatted_lines.append(f"- {question}: {answer_str}")
        
        return "\n".join(formatted_lines)
    
    except Exception as e:
        logger.exception(f"Error formatting case details: {e}")
        return "Error formatting case details."


def format_details_for_prompt(details: dict[str, Any]) -> str:
    """
    Format structured case details into a readable string for the prompt.

    Args:
        details: Dictionary containing structured case information with keys:
                 - case_details: Basic case information
                 - resolve_answers: Question-answer , options pairs from resolve
                 - resolve_result: Recommendation result (title, summary, version)
                 - kyc_details: Optional KYC question-answer , options pairs

    Returns:
        Formatted string of all case details
    """
    try:
        if not details:
            return "No details available."
        
        formatted_sections = []
        
        # Format Case Details section
        case_details = details.get("case_details", {})
        if case_details:
            formatted_sections.append("=== CASE INFORMATION ===")
            for key, value in case_details.items():
                formatted_key = key.replace("_", " ").title()
                formatted_sections.append(f"{formatted_key}: {value}")
            formatted_sections.append("")
        
        # Format Triage Details section (if present)
        triage_details = details.get("triage_details", {})
        if triage_details:
            formatted_sections.append("=== TRIAGE INFORMATION ===")
            customer_name = triage_details.get("customer_name", "")
            if isinstance(triage_details, dict):
                for item in triage_details.get("triage_answers", []):
                    question = item.get("question", "")
                    answer = item.get("answer", "")
                    options = item.get("options")
                    answer_str = str(answer) if answer else "Not provided"
                    formatted_sections.append(f"Question: {question}")
                    if options:
                        formatted_sections.append("Options:")
                        if isinstance(options, list):
                            for idx, opt in enumerate(options, start=1):
                                formatted_sections.append(f"{idx}) {opt}")
                        else:
                            formatted_sections.append(f"1) {options}")
                    formatted_sections.append(f"Answer: {answer_str}")
                    formatted_sections.append("")

                formatted_sections.append(f"Question: Name of the client")
                formatted_sections.append(f"Answer: {customer_name}")
                formatted_sections.append("")

        # Format KYC Details section (if present)
        kyc_details = details.get("kyc_details", {})
        if kyc_details:
            formatted_sections.append("=== CLIENT INFORMATION (KYC) ===")
            # Handle both list format (new) and dict format (old) for backward compatibility
            if isinstance(kyc_details, list):
                for item in kyc_details:
                    question = item.get("question", "")
                    answer = item.get("answer", "")
                    options = item.get("options")
                    answer_str = str(answer) if answer else "Not provided"
                    formatted_sections.append(f"Question: {question}")
                    if options:
                        formatted_sections.append("Options:")
                        if isinstance(options, list):
                            for idx, opt in enumerate(options, start=1):
                                formatted_sections.append(f"{idx}) {opt}")
                        else:
                            formatted_sections.append(f"1) {options}")
                    formatted_sections.append(f"Answer: {answer_str}")
                    formatted_sections.append("")
            else:
                # Old dict format for backward compatibility
                for question, answer in kyc_details.items():
                    answer_str = str(answer) if answer else "Not provided"
                    formatted_sections.append(f"Question: {question}")
                    formatted_sections.append(f"Answer: {answer_str}")
                    formatted_sections.append("")
        
        # Format Resolve Answers section
        resolve_answers = details.get("resolve_answers", {})
        if resolve_answers:
            formatted_sections.append("=== DISPUTE RESOLUTION QUESTIONNAIRE ===")
            # Handle both list format (new) and dict format (old) for backward compatibility
            if isinstance(resolve_answers, list):
                for item in resolve_answers:
                    question = item.get("question", "")
                    answer = item.get("answer", "")
                    options = item.get("options")
                    answer_str = str(answer) if answer else "Not provided"
                    formatted_sections.append(f"Question: {question}")
                    if options:
                        formatted_sections.append("Options:")
                        if isinstance(options, list):
                            for idx, opt in enumerate(options, start=1):
                                formatted_sections.append(f"{idx}) {opt}")
                        else:
                            formatted_sections.append(f"1) {options}")
                    formatted_sections.append(f"Answer: {answer_str}")
                    formatted_sections.append("")
            else:
                # Old dict format for backward compatibility
                for question, answer in resolve_answers.items():
                    answer_str = str(answer) if answer else "Not provided"
                    formatted_sections.append(f"Question: {question}")
                    formatted_sections.append(f"Answer: {answer_str}")
                    formatted_sections.append("")
        
        # Format Recommended Approach section
        recommended_approach = details.get("recommended_approach", {})
        if recommended_approach:
            formatted_sections.append("=== RECOMMENDED approach ===")
            formatted_sections.append(f"Recommendation: {recommended_approach.get('title', 'N/A')}")
            formatted_sections.append(f"{recommended_approach.get('summary', 'N/A')}")
            formatted_sections.append("")
        
        # Format Resolve Result section
        resolve_result = details.get("resolve_result", {})
        if resolve_result:
            formatted_sections.append("=== BEST FIT Pathway ===")
            formatted_sections.append(f"Recommendation: {resolve_result.get('title', 'N/A')}")
            formatted_sections.append(f"{resolve_result.get('summary', 'N/A')}")
            formatted_sections.append("")
        
        return "\n".join(formatted_sections)
    
    except Exception as e:
        logger.exception(f"Error formatting details: {e}")
        return "Error formatting details."


async def generate_ai_case_summary(
    case: Case,
    case_type: CaseTypeEnum,
    details: dict[str, Any],
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None
) -> dict[str, Any]:
    """
    Generate AI-powered case summary using OpenAI based on structured case details.

    This function:
    1. Loads the YAML prompt template
    2. Formats the structured details for the prompt
    3. Calls OpenAI API to generate summary with retry mechanism
    4. Returns the generated summary in JSON format
    5. Retries up to 3 times with 3-second delays on failure
    6. Returns hardcoded response if all retries fail

    Args:
        details: Dictionary containing structured case information with keys:
                 - case_details: Basic case information (case_number, case_type, etc.)
                 - resolve_answers: Question-answer pairs from dispute resolution questionnaire
                 - resolve_result: Recommended resolution approach (title, summary, version)
                 - kyc_details: Optional KYC question-answer pairs (client information)
        temperature: Optional temperature for AI generation (overrides YAML config)
        max_tokens: Optional max tokens for AI generation (overrides YAML config)
        model: Optional model name (overrides YAML config)

    Returns:
        Dictionary containing:
            - case_summary: List of dictionaries with 'title' and 'description' fields
                           Typically contains 5 sections: Client Information, Case Overview,
                           Relationship Dynamics, Financial Considerations, Recommended Approach
            - status: Status of the generation
            - model_used: Model name used
            - template_used: Template name used
            - retry_count: Number of retries attempted

    Raises:
        ValueError: If details are empty or invalid
        FileNotFoundError: If YAML template not found
    """
    import asyncio
    import json
    
    MAX_RETRIES = 3
    RETRY_DELAY = 3  # seconds
    
    # Hardcoded fallback response
    FALLBACK_RESPONSE = {
        "case_summary": [
            {
                "title": "Error",
                "description": "AI summary generation failed after multiple attempts. Please try again later."
            },
            {
                "title": "Action Required",
                "description": "Please review the case details manually and contact support if this issue persists."
            }
        ],
        "status": False,
        "model_used": "N/A",
        "template_used": "case_summary_prompt",
        "retry_count": MAX_RETRIES,
    }
    
    try:
        # Validate details
        if not details or not isinstance(details, dict):
            raise ValueError("Details must be a non-empty dictionary")
        
        # Load YAML template
        # template_path = settings.CASE_SUMMARY_PROMPT_PATH
        if case.is_triage is True:
            template_path = f"{settings.CASE_SUMMARY_PROMPT_PATH}/triage_case_summary_prompt.yaml"
        else:
            template_path = get_prompt_template_path(case_type)
        yaml_config = load_yaml_prompt_template(template_path)
        
        # Get prompt configuration
        prompt_config = yaml_config.get("case_summary_prompt", {})
        if not prompt_config:
            raise ValueError("Missing 'case_summary_prompt' in YAML template")
        
        system_message = prompt_config.get("system_message", "")
        user_message_template = prompt_config.get("user_message_template", "")
        
        # Get config values (prefer parameters, fallback to YAML, then to defaults)
        final_temperature = temperature if temperature is not None else prompt_config.get("temperature", settings.CASE_SUMMARY_TEMPERATURE)
        final_max_tokens = max_tokens if max_tokens is not None else prompt_config.get("max_tokens", settings.CASE_SUMMARY_MAX_TOKENS)
        final_model = model if model is not None else prompt_config.get("model", settings.DEFAULT_CASE_SUMMARY_MODEL)
        
        # Format details for the prompt
        formatted_details = format_details_for_prompt(details)
        
        # Prepare data for placeholder replacement
        placeholder_data = {
            "case_details": formatted_details,
        }
        # Fill template with actual data
        filled_user_message = fill_prompt_placeholders(user_message_template, placeholder_data)
        # Initialize LLM agent
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key is not set")

        llm_agent = LLMAgent(api_key=api_key, model=final_model)
        
        # Retry mechanism
        retry_count = 0
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempting to generate AI case summary (attempt {attempt + 1}/{MAX_RETRIES})")
                
                # Generate summary using the LLM agent
                summary_response = await llm_agent.generate_case_summary(
                    system_message=system_message,
                    user_message=filled_user_message,
                    temperature=final_temperature,
                    max_tokens=final_max_tokens,
                    model=final_model
                )
                
                # Validate response
                if not summary_response or summary_response.strip() == "":
                    raise ValueError("Empty response from AI")
                
                # Try to parse as JSON
                try:
                    # Clean the response (remove markdown code blocks if present)
                    cleaned_response = summary_response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response.replace("```", "").strip()
                    
                    summary_json = json.loads(cleaned_response)
                    
                    # Validate JSON structure
                    if not isinstance(summary_json, dict):
                        raise ValueError("AI response is not a valid JSON object")
                    
                    # Validate case_summary array exists
                    case_summary = summary_json.get("case_summary", [])
                    if not isinstance(case_summary, list) or len(case_summary) == 0:
                        raise ValueError("AI response missing valid 'case_summary' array")
                    
                    # Success - return the parsed JSON
                    logger.info(f"Successfully generated AI case summary on attempt {attempt + 1}")
                    return {
                        "case_summary": case_summary,
                        "status": True,
                        "model_used": final_model,
                        "template_used": "case_summary_prompt",
                        "retry_count": attempt,
                    }
                    
                except json.JSONDecodeError as json_err:
                    logger.warning(f"Failed to parse AI response as JSON on attempt {attempt + 1}: {json_err}")
                    # If JSON parsing fails, treat it as a failed attempt
                    raise ValueError(f"Invalid JSON response from AI: {json_err}")
                
            except Exception as attempt_error:
                last_error = attempt_error
                retry_count = attempt + 1
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {attempt_error}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Waiting {RETRY_DELAY} seconds before retry...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed. Returning fallback response.")
        
        # All retries failed - return hardcoded response
        logger.error(f"Failed to generate AI case summary after {MAX_RETRIES} attempts. Last error: {last_error}")
        return FALLBACK_RESPONSE
    
    except ValueError:
        raise
    except Exception as e:
        logger.exception(f"Error generating AI case summary: {e}")
        # Return fallback response instead of raising
        return FALLBACK_RESPONSE


async def generate_ai_recommendation(
    details: dict[str, Any],
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None
) -> dict[str, Any]:
    """
    Generate AI-powered recommendation using OpenAI based on structured case details.

    This function:
    1. Loads the YAML prompt template
    2. Formats the structured details for the prompt
    3. Calls OpenAI API to generate recommendation with retry mechanism
    4. Returns the generated recommendation in JSON format
    5. Retries up to 3 times with 3-second delays on failure
    6. Returns hardcoded response if all retries fail

    Args:
        details: Dictionary containing structured case information with keys:
                 - resolve_question_answers: Question-answer pairs from dispute resolution questionnaire
                 - recommended_approach: Recommended resolution approach (title, summary, version)
        temperature: Optional temperature for AI generation (overrides YAML config)
        max_tokens: Optional max tokens for AI generation (overrides YAML config)
        model: Optional model name (overrides YAML config)

    Returns:
        Dictionary containing:
            - personalised_analysis: List of dictionaries with 'title' and 'description' fields

    Raises:
        ValueError: If details are empty or invalid
        FileNotFoundError: If YAML template not found
    """
    import asyncio
    import json
    
    MAX_RETRIES = 3
    RETRY_DELAY = 3  # seconds
    
    # Hardcoded fallback response
    FALLBACK_RESPONSE = {
        "personalised_analysis": [
            {
                "title": "Error",
                "description": "AI recommendation generation failed after multiple attempts. Please try again later."
            },
            {
                "title": "Action Required",
                "description": "Please review the case details manually and contact support if this issue persists."
            }
        ],
        "status": False,
        "model_used": "N/A",
        "template_used": "ai_recommendation_prompt",
        "retry_count": MAX_RETRIES,
    }
    
    try:
        # Validate details
        if not details or not isinstance(details, dict):
            raise ValueError("Details must be a non-empty dictionary")
        
        # Load YAML template
        template_path = f"{settings.RESOLVE_RECOMMENDATION_PROMPT_PATH}/resolve_recommendation_prompt.yaml"
        # template_path = get_prompt_template_path(case_type)
        yaml_config = load_yaml_prompt_template(template_path)
        
        # Get prompt configuration
        prompt_config = yaml_config.get("resolve_recommendation_prompt", {})
        if not prompt_config:
            raise ValueError("Missing 'resolve_recommendation_prompt' in YAML template")
        
        system_message = prompt_config.get("system_message", "")
        user_message_template = prompt_config.get("user_message_template", "")
        
        # Get config values (prefer parameters, fallback to YAML, then to defaults)
        final_temperature = temperature if temperature is not None else prompt_config.get("temperature", settings.CASE_SUMMARY_TEMPERATURE)
        final_max_tokens = max_tokens if max_tokens is not None else prompt_config.get("max_tokens", settings.CASE_SUMMARY_MAX_TOKENS)
        final_model = model if model is not None else prompt_config.get("model", settings.DEFAULT_CASE_SUMMARY_MODEL)
        
        # Format details for the prompt
        formatted_details = format_details_for_prompt(details)
        
        # Prepare data for placeholder replacement
        placeholder_data = {
            "details": formatted_details,
        }
        # Fill template with actual data
        filled_user_message = fill_prompt_placeholders(user_message_template, placeholder_data)
        # Initialize LLM agent
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key is not set")

        llm_agent = LLMAgent(api_key=api_key, model=final_model)
        
        # Retry mechanism
        retry_count = 0
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempting to generate AI recommendation (attempt {attempt + 1}/{MAX_RETRIES})")
                
                # Generate summary using the LLM agent
                summary_response = await llm_agent.generate_case_summary(
                    system_message=system_message,
                    user_message=filled_user_message,
                    temperature=final_temperature,
                    max_tokens=final_max_tokens,
                    model=final_model
                )
                
                # Validate response
                if not summary_response or summary_response.strip() == "":
                    raise ValueError("Empty response from AI")
                
                # Try to parse as JSON
                try:
                    # Clean the response (remove markdown code blocks if present)
                    cleaned_response = summary_response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response.replace("```", "").strip()
                    
                    summary_json = json.loads(cleaned_response)
                    # Validate JSON structure
                    if not isinstance(summary_json, dict):
                        raise ValueError("AI response is not a valid JSON object")
                    
                    # Validate case_summary array exists
                    personalised_analysis = summary_json.get("personalised_analysis", [])
                    if not isinstance(personalised_analysis, list) or len(personalised_analysis) == 0:
                        raise ValueError("AI response missing valid 'case_summary' array")
                    
                    # Success - return the parsed JSON
                    logger.info(f"Successfully generated AI case summary on attempt {attempt + 1}")
                    return {
                        "personalised_analysis": personalised_analysis,
                        "status": True,
                        "model_used": final_model,
                        "template_used": "resolve_recommendation_prompt",
                        "retry_count": attempt,
                    }
                    
                except json.JSONDecodeError as json_err:
                    logger.warning(f"Failed to parse AI response as JSON on attempt {attempt + 1}: {json_err}")
                    # If JSON parsing fails, treat it as a failed attempt
                    raise ValueError(f"Invalid JSON response from AI: {json_err}")
                
            except Exception as attempt_error:
                last_error = attempt_error
                retry_count = attempt + 1
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {attempt_error}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Waiting {RETRY_DELAY} seconds before retry...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed. Returning fallback response.")
        
        # All retries failed - return hardcoded response
        logger.error(f"Failed to generate AI recommendation after {MAX_RETRIES} attempts. Last error: {last_error}")
        return FALLBACK_RESPONSE
    
    except ValueError:
        raise
    except Exception as e:
        logger.exception(f"Error generating AI recommendation: {e}")
        # Return fallback response instead of raising
        return FALLBACK_RESPONSE

