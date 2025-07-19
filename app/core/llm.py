import json
import time
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict
from app.core.config import llm_client


class Outfit(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    SPORTY = "sporty"
    GOTH = "goth"
    BOHEMIAN = "bohemian"
    VINTAGE = "vintage"
    STREETWEAR = "streetwear"
    BUSINESS = "business"


class LifeProblem(str, Enum):
    RELATIONSHIP_ISSUES = "relationship issues"
    CAREER_STAGNATION = "career stagnation"
    FINANCIAL_STRESS = "financial stress"
    IDENTITY_CRISIS = "identity crisis"
    FAMILY_CONFLICT = "family conflict"
    HEALTH_CONCERNS = "health concerns"
    SOCIAL_ISOLATION = "social isolation"
    ADDICTION = "addiction struggles"


class MentalState(str, Enum):
    ANXIOUS = "anxious"
    DEPRESSED = "depressed"
    ANGRY = "angry"
    CONFUSED = "confused"
    HOPEFUL = "hopeful"
    EXHAUSTED = "exhausted"
    NUMB = "numb"
    OVERWHELMED = "overwhelmed"


class CharacterAccessories(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hat: Optional[str]
    glasses: Optional[str]
    jewelry: Optional[str]
    bag: Optional[str]
    other: Optional[str]


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    background: str
    outfit: Outfit
    shirt: str
    accessories: CharacterAccessories
    problems: List[LifeProblem]
    mental_state: MentalState
    interaction_warning: str


class CharacterGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str
    characters: List[Character]


async def generate_characters_from_theme(theme: str) -> CharacterGenerationResponse:
    """
    Generate a list of characters based on a given theme.

    Args:
        theme (str): The main theme for character generation

    Returns:
        CharacterGenerationResponse: Generated characters with all attributes
    """

    # Example JSON schema for the response:
    # {
    #     "theme": "urban dystopia",
    #     "characters": [
    #         {
    #             "name": "Marcus Chen",
    #             "background": "Former tech executive who lost everything in the market crash...",
    #             "outfit": "streetwear",
    #             "shirt": "Faded black hoodie with torn sleeves",
    #             "accessories": {
    #                 "hat": "Worn baseball cap",
    #                 "glasses": null,
    #                 "jewelry": "Simple silver chain",
    #                 "bag": "Messenger bag with patches",
    #                 "other": null
    #             },
    #             "problems": ["financial stress", "identity crisis"],
    #             "mental_state": "numb",
    #             "interaction_warning": "Avoid discussing money or past success."
    #         }
    #     ]
    # }

    response_schema = CharacterGenerationResponse.model_json_schema(mode="validation")

    system_prompt = """You are a creative character designer. Generate diverse, complex characters based on the given theme.
    
    IMPORTANT: You MUST use ONLY the exact values provided in the lists for outfits, problems, and mental states.
    Do NOT create new categories or variations. Characters should feel real but must fit within these constraints.
    
    For each character, provide:
    - A unique name
    - A detailed background story
    - Their outfit style (MUST be one of the provided options)
    - A specific shirt description
    - Accessories (can be null or descriptive strings)
    - Life problems (MUST be from the provided list only)
    - Current mental state (MUST be one of the provided options)
    - A warning about interaction triggers
    
    Return valid JSON that can be parsed by Python's json.loads()."""

    user_prompt = f"""Generate 3-5 characters for the theme: "{theme}"

    Ensure characters use ONLY these options:
    - Outfits: {', '.join([outfit.value for outfit in Outfit])}
    - Problems: {', '.join([problem.value for problem in LifeProblem])}
    - Mental states: {', '.join([state.value for state in MentalState])}

    The response must follow this exact JSON schema:
    {json.dumps(response_schema, indent=2)}"""

    start_time = time.time()

    response = await llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "character_generation",
                "schema": response_schema,
                "strict": True,
            },
        },
    )

    end_time = time.time()
    latency = end_time - start_time
    print(f"Character generation latency: {latency:.2f} seconds")

    result = json.loads(response.choices[0].message.content)

    return CharacterGenerationResponse(**result)
