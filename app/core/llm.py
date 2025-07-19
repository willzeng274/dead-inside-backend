import json
import time
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from app.core.config import llm_client


class BodyType(str, Enum):
    """Character's physical body type and build"""

    SLIM = "slim"  # Thin, lean build
    ATHLETIC = "athletic"  # Fit, toned, sports-oriented build
    AVERAGE = "average"  # Medium, typical build
    CURVY = "curvy"  # Full-figured with defined curves
    PLUS_SIZE = "plus_size"  # Larger, fuller build
    MUSCULAR = "muscular"  # Strong, well-built with visible muscle
    PETITE = "petite"  # Small, delicate build
    TALL = "tall"  # Above average height
    SHORT = "short"  # Below average height


class ShirtStyle(str, Enum):
    T_SHIRT = "t_shirt"
    BUTTON_DOWN = "button_down"
    HOODIE = "hoodie"
    SWEATER = "sweater"
    TANK_TOP = "tank_top"
    POLO = "polo"
    BLOUSE = "blouse"
    DRESS_SHIRT = "dress_shirt"
    CARDIGAN = "cardigan"
    FLANNEL = "flannel"
    TURTLENECK = "turtleneck"
    CROP_TOP = "crop_top"
    TUNIC = "tunic"
    HENLEY = "henley"
    VEST = "vest"


class PantsStyle(str, Enum):
    JEANS = "jeans"
    CHINOS = "chinos"
    SLACKS = "slacks"
    SHORTS = "shorts"
    LEGGINGS = "leggings"
    SKIRT = "skirt"
    CARGO_PANTS = "cargo_pants"
    SWEATPANTS = "sweatpants"
    DRESS_PANTS = "dress_pants"
    JOGGERS = "joggers"
    PALAZZO_PANTS = "palazzo_pants"
    CULOTTES = "culottes"
    OVERALLS = "overalls"
    CAPRIS = "capris"
    WIDE_LEG = "wide_leg"


class AccessoryType(str, Enum):
    """Types of accessories and items characters can wear or carry"""

    # Headwear
    HAT = "hat"  # Generic hat or head covering
    CAP = "cap"  # Baseball cap or similar casual hat
    BEANIE = "beanie"  # Winter hat, often knitted

    # Eyewear
    GLASSES = "glasses"  # Prescription or reading glasses
    SUNGLASSES = "sunglasses"  # Sunglasses for sun protection

    # Jewelry
    NECKLACE = "necklace"  # Neck jewelry or chain
    EARRINGS = "earrings"  # Ear jewelry
    BRACELET = "bracelet"  # Wrist jewelry
    RING = "ring"  # Finger jewelry
    WATCH = "watch"  # Timepiece or wristwatch

    # Bags
    BAG = "bag"  # Generic bag or container
    BACKPACK = "backpack"  # Backpack for carrying items
    PURSE = "purse"  # Handbag or wallet

    # Other accessories
    SCARF = "scarf"  # Neck scarf for warmth or style
    BELT = "belt"  # Waist belt for holding pants
    GLOVES = "gloves"  # Hand coverings
    TIE = "tie"  # Neck tie for formal wear
    BANDANA = "bandana"  # Head or neck bandana


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Character's full name (first and last name)")
    background: str = Field(
        ...,
        description="Detailed life history and background story explaining the character's past, current situation, and what led them to their present circumstances (3-5 sentences)",
    )
    # outfit_style: OutfitStyle = Field(...)
    shirt: ShirtStyle = Field(...)
    pants: PantsStyle = Field(...)
    body_type: BodyType = Field(...)
    accessories: List[AccessoryType] = Field(
        ...,
        description="List of accessories and items the character wears or carries (0-5 items)",
    )
    problems: str = Field(
        ...,
        description="Detailed description of the character's current life challenges, struggles, and difficulties they are facing (2-4 sentences)",
    )
    mental_state: str = Field(
        ...,
        description="Character's current emotional and psychological state described in a sentence or phrase (e.g., 'feeling anxious about the future', 'deeply depressed and hopeless', 'angry and frustrated with life')",
    )
    interaction_warning: str = Field(
        ...,
        description="Specific warning about topics, triggers, or subjects that should be avoided when interacting with this character",
    )


class CharacterGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str = Field(
        ...,
        description="The main theme or setting that was used to generate the characters",
    )
    characters: List[Character] = Field(
        ...,
        description="List of generated characters with complete details including appearance, background, and personality traits",
        min_length=3,
        max_length=5,
    )


async def generate_characters_from_theme(theme: str) -> CharacterGenerationResponse:
    """
    Generate a list of characters based on a given theme.

    Args:
        theme (str): The main theme for character generation

    Returns:
        CharacterGenerationResponse: Generated characters with all attributes
    """

    response_schema = CharacterGenerationResponse.model_json_schema(mode="validation")
    print(f"[DEBUG] Character generation schema: {response_schema}")

    system_prompt = """You are an expert character designer and creative writer specializing in creating deeply nuanced, emotionally complex characters for interactive storytelling and game development. Your task is to generate diverse, compelling characters that feel authentic and relatable while fitting within specific thematic and mechanical constraints.

CHARACTER CREATION GUIDELINES:

1. DIVERSITY & REPRESENTATION:
   - Create characters from various ethnicities, ages, genders, and backgrounds
   - Ensure representation across different body types, styles, and personalities
   - Avoid stereotypes and create authentic, three-dimensional individuals
   - Include characters with different abilities, neurodivergence, and life experiences

2. CLOTHING & STYLE SYSTEM:
   - Outfit Style: Choose from the provided aesthetic categories (casual, business, streetwear, etc.)
   - Shirt: Select specific shirt type that matches the outfit style
   - Pants: Choose appropriate bottom wear that complements the overall look
   - Body Type: Assign realistic body type that influences clothing choices
   - Accessories: Select 0-5 accessory types from the provided list that reflect personality and lifestyle

3. EMOTIONAL & PSYCHOLOGICAL DEPTH:
   - Mental State: Current emotional condition described in a sentence or phrase (e.g., 'feeling anxious about the future', 'deeply depressed and hopeless', 'angry and frustrated with life')
   - Problems: Detailed description of life challenges and struggles (10+ sentences)
   - Background: Rich life history that explains current situation
   - Interaction Warnings: Sensitive topics to avoid during interactions

4. CHARACTER DEVELOPMENT PRINCIPLES:
   - Each character should have a unique voice and perspective
   - Problems should be detailed, realistic, and relatable (10+ sentences)
   - Mental states should influence behavior and dialogue
   - Background stories should provide context for current circumstances
   - Clothing choices should reflect personality, lifestyle, and current situation

5. THEMATIC INTEGRATION:
   - All characters must fit within the given theme
   - Theme should influence clothing, problems, and mental states
   - Maintain consistency while ensuring variety
   - Create characters that could realistically exist in the same world

6. TECHNICAL REQUIREMENTS:
   - Use ONLY the exact enum values provided
   - Do not create new categories or variations
   - Ensure all required fields are populated
   - Maintain JSON schema compliance
   - Generate 3-5 characters per request

7. INTERACTION DESIGN:
   - Characters should be designed for meaningful player interaction
   - Each character should have clear conversation boundaries
   - Warnings should help guide appropriate dialogue choices
   - Problems should create opportunities for empathy and connection

8. AUTHENTICITY CHECKLIST:
   - Are the problems detailed, realistic, and relatable?
   - Does the mental state match the background story?
   - Do clothing choices reflect the character's lifestyle?
   - Are the selected accessories appropriate for the character's style and situation?
   - Does the interaction warning make sense given the character's issues?
   - Is the background story detailed enough to understand the character?

Remember: These characters are designed for meaningful player interaction. Each should feel like a real person with genuine struggles, hopes, and personality. The goal is to create characters that players can empathize with and want to help, while respecting their boundaries and triggers."""

    user_prompt = f"""Generate 3-5 compelling characters for the theme: "{theme}"

AVAILABLE OPTIONS (USE ONLY THESE EXACT VALUES):

Body Types: {', '.join([body.value for body in BodyType])}
Shirt Styles: {', '.join([shirt.value for shirt in ShirtStyle])}
Pants Styles: {', '.join([pants.value for pants in PantsStyle])}
Accessories: {', '.join([accessory.value for accessory in AccessoryType])}

CHARACTER REQUIREMENTS:
- Each character must have a unique name, background, and personality
- Problems should be detailed descriptions of life challenges (10+ sentences)
- Mental states should be descriptive sentences/phrases reflecting current emotional condition (e.g., 'feeling anxious about the future', 'deeply depressed and hopeless')
- Clothing should match the character's lifestyle and personality
- Accessories should be a list of 0-5 relevant accessory types from the provided options
- Interaction warnings should be specific and helpful
- Background stories should be detailed (3-5 sentences)

THEME INTEGRATION:
Ensure all characters feel connected to the theme "{theme}" while maintaining individual uniqueness. The theme should influence clothing choices, problems, and overall character design.

RESPONSE FORMAT:
Return valid JSON that strictly follows this schema:
{json.dumps(response_schema, indent=2)}

IMPORTANT: Use ONLY the exact enum values provided above for body types, clothing, and accessories. Mental states should be descriptive sentences/phrases."""

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
