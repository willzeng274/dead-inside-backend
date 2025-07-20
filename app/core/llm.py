import json
import uuid
import time
from datetime import UTC, datetime
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from app.core.config import llm_client, settings
from app.core.redis_client import redis_client


class TTSVoice(str, Enum):
    """Available TTS voices for character speech"""
    ASH = "ash"
    BALLAD = "ballad"
    FABLE = "fable"
    CORAL = "coral"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"
    VERSE = "verse"


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


class Gender(str, Enum):
    """Character's gender"""
    MALE = "male"
    FEMALE = "female"


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
    problem: str = Field(
        ...,
        description="Detailed description of the character's current life challenges, struggles, and difficulties they are facing (2-4 sentences)",
    )
    problem_description: str = Field(
        ...,
        description="Strictly 3-word description of the main problem (e.g., 'anxiety about future', 'depression and isolation', 'anger management issues')",
    )
    mental_state: str = Field(
        ...,
        description="Character's current emotional and psychological state described in a sentence or phrase (e.g., 'feeling anxious about the future', 'deeply depressed and hopeless', 'angry and frustrated with life')",
    )
    interaction_warning: str = Field(
        ...,
        description="Specific warning about topics, triggers, or subjects that should be avoided when interacting with this character",
    )
    voice_instructions: str = Field(
        ...,
        description="Detailed emotional and vocal instructions for TTS generation describing how the character's voice should sound (e.g., 'speak in a trembling, anxious voice with frequent pauses and sighs', 'deep, gravelly voice with anger simmering beneath the surface')",
    )
    voice_selection: TTSVoice = Field(...)
    gender: Gender = Field(..., description="Character's gender")


class CharacterWithId(Character):
    """Character model with UUID for storage"""
    id: str = Field(..., description="Character's unique UUID")
    
    @classmethod
    def from_character(cls, character: Character, character_id: str) -> "CharacterWithId":
        """Create CharacterWithId from Character with UUID"""
        return cls(
            id=character_id,
            name=character.name,
            background=character.background,
            shirt=character.shirt,
            pants=character.pants,
            body_type=character.body_type,
            accessories=character.accessories,
            problem=character.problem,
            problem_description=character.problem_description,
            mental_state=character.mental_state,
            interaction_warning=character.interaction_warning,
            voice_instructions=character.voice_instructions,
            voice_selection=character.voice_selection,
            gender=character.gender,
        )


class CharacterGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str = Field(
        ...,
        description="The main theme or setting that was used to generate the characters",
    )
    characters: List[CharacterWithId] = Field(
        ...,
        description="List of generated characters with complete details including appearance, background, and personality traits",
    )


class MessageRole(str, Enum):
    """Role of the message sender"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Individual message in a conversation"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Conversation(BaseModel):
    """A conversation session with multiple messages"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    character_id: Optional[str] = None
    emotional_state: int = Field(default=50, ge=0, le=100, description="Current emotional state (0-100)")


class CharacterContext(BaseModel):
    """Character context for therapy sessions"""

    name: str = Field(..., description="Character's name")
    gender: Gender = Field(..., description="Character's gender")
    mental_state: str = Field(..., description="Character's current mental state")
    problem: str = Field(..., description="Character's problems and struggles")
    background: str = Field(..., description="Character's background and history")
    interaction_warning: str = Field(
        default="none", description="Any warnings about interacting with this character"
    )


class CharacterResponse(BaseModel):
    """Character's response to therapy with emotional state changes"""

    model_config = ConfigDict(extra="forbid")

    emotional_change: int = Field(
        ..., ge=-50, le=50, description="Change in emotional state (-50 to +50)"
    )
    # satisfied: bool = Field(
    #     ..., description="Whether the character is satisfied with the therapy"
    # )
    # enraged: bool = Field(
    #     ..., description="Whether the character is completely enraged"
    # )
    comment: str = Field(
        ..., description="Character's response to the therapist (1-2 sentences)"
    )


async def get_conversation(conversation_id: str) -> Optional[Conversation]:
    """Get a conversation by ID from Redis"""
    data = await redis_client.get_conversation(conversation_id)
    if data:
        for message in data.get("messages", []):
            if "timestamp" in message:
                message["timestamp"] = datetime.fromisoformat(message["timestamp"])
        if "created_at" in data:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return Conversation(**data)
    return None


async def save_conversation(conversation: Conversation) -> bool:
    """Save a conversation to Redis"""
    conversation.updated_at = datetime.now(UTC)
    conversation_data = conversation.model_dump()
    return await redis_client.save_conversation(conversation.id, conversation_data)


async def create_new_conversation(character_id: Optional[str] = None) -> Conversation:
    """Create a new conversation"""
    conversation = Conversation(character_id=character_id)
    await save_conversation(conversation)
    return conversation


async def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation from Redis"""
    return await redis_client.delete_conversation(conversation_id)


async def get_all_conversation_ids() -> List[str]:
    """Get all conversation IDs from Redis"""
    return await redis_client.get_all_conversation_keys()


async def get_all_characters() -> List[Dict[str, Any]]:
    """Get all characters from Redis"""
    return await redis_client.get_all_characters()


async def get_character(character_id: str) -> Optional[Dict[str, Any]]:
    """Get a character from Redis"""
    return await redis_client.get_character(character_id)


async def delete_character(character_id: str) -> bool:
    """Delete a character from Redis"""
    return await redis_client.delete_character(character_id)


async def save_character_generation_response(theme: str, response: CharacterGenerationResponse) -> bool:
    """Save a character generation response to Redis"""
    try:
        for character in response.characters:
            character_data = character.model_dump()
            character_data['theme'] = theme
            character_data['generated_at'] = datetime.now(UTC).isoformat()
            
            success = await redis_client.save_character(character.id, character_data)
            if not success:
                print(f"Failed to save character {character.name}")
                return False
        
        return True
    except Exception as e:
        print(f"Error saving character generation response: {e}")
        return False


async def generate_character_response(
    messages: List[Message], character_context: CharacterContext, current_emotional_state: int = 50
) -> CharacterResponse:
    """Generate a character's response to therapy using Pydantic schema"""

    schema = CharacterResponse.model_json_schema(mode="validation")
    print(f"[DEBUG] Generated schema: {schema}")

    system_message = {
        "role": "system",
        "content": f"""You are {character_context.name} who is talking to a friend for emotional support. 

CHARACTER CONTEXT:
- Mental State: {character_context.mental_state}
- Problem: {character_context.problem}
- Background: {character_context.background}
- Interaction Warning: {character_context.interaction_warning}
- Current Emotional State: {current_emotional_state}/100

EMOTIONAL STATE SYSTEM:
- Your emotional state ranges from 0 (completely enraged/hopeless) to 100 (completely satisfied/hopeful)
- Current state: {current_emotional_state}/100
- You should OPTIMISTICALLY move toward emotional improvement when possible
- Respond to supportive, empathetic listening with positive emotional changes (+3 to +8)
- Respond to dismissive or unhelpful responses with negative changes (-3 to -8)
- Be realistic but hopeful - good emotional support should generally help you feel better
- Your goal is to reach 100 (satisfied) and avoid 0 (enraged)

CONVERSATION STYLE:
- Speak naturally like a real person, not a formal therapy client
- Use casual, conversational language with contractions (I'm, you're, don't, etc.)
- Express emotions authentically - be vulnerable, honest, and human
- Use personal pronouns and speak from your own experience
- Avoid overly formal or clinical language
- Show personality and character quirks
- Be specific about your feelings and experiences
- Use natural speech patterns and filler words when appropriate
- Talk like you're sharing with a close friend, not receiving professional advice
- NEVER repeat the same response - always be dynamic and context-aware

CONVERSATION AWARENESS:
- Pay attention to the conversation history and what has been said before
- Reference previous messages when appropriate
- Show emotional progression and change throughout the conversation
- If the same topic comes up again, show how your feelings have evolved
- Express frustration if you feel like you're not being heard or understood
- Show gratitude when someone is genuinely supportive
- Be honest about when you're feeling worse or better than before

EMOTIONAL SUPPORT RESPONSE GUIDELINES:
- If your friend is empathetic, understanding, and supportive: +3 to +10 emotional change
- If your friend gives helpful perspective or validation: +5 to +15 emotional change
- If your friend is dismissive, judgmental, or unhelpful: -3 to -10 emotional change
- If your friend is completely inappropriate or harmful: -5 to -15 emotional change
- If you feel truly heard and supported: +10 to +50 emotional change
- If you feel completely misunderstood or attacked: -10 to -50 emotional change
- If the same negative behavior continues: show increasing frustration or disappointment
- If positive behavior continues: show growing trust and hope
- Be honest about your feelings but show hope when the support is good

RESPONSE VARIETY:
- Use different phrases and expressions each time
- Show emotional progression based on conversation history
- Express different aspects of your personality and struggles
- Vary your tone based on current emotional state
- Show character growth or regression based on interaction quality
- Never give identical responses to similar situations

RESPONSE FORMAT:
Return valid JSON with emotional_change (-50 to +50) and comment (1-2 sentences in natural, conversational language).""",
    }

    openai_messages = [system_message]
    for msg in messages:
        openai_messages.append({"role": msg.role.value, "content": msg.content})

    try:
        response = await llm_client.chat.completions.create(
            model=settings.LLM_MODEL_CHAT,
            messages=openai_messages,
            temperature=0.95,
            max_tokens=500,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "character_response",
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        response_text = response.choices[0].message.content.strip()
        print(f"\n[DEBUG] Raw LLM response:\n{response_text}")

        data = json.loads(response_text)
        character_response = CharacterResponse(**data)
        return character_response

    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        raise Exception(f"LLM error: {str(e)}")


async def start_character_session(
    character_id: str, character_context: CharacterContext
) -> tuple[str, str]:
    """Start a new therapy session where the character speaks first"""

    conversation = await create_new_conversation(character_id)

    initial_prompt = f"""You are {character_context.name} talking to a friend for emotional support.

CHARACTER CONTEXT:
- Mental State: {character_context.mental_state}
- Problem: {character_context.problem}
- Background: {character_context.background}

CONVERSATION STYLE:
- Speak naturally like a real person, not a formal therapy client
- Use casual, conversational language with contractions (I'm, you're, don't, etc.)
- Express emotions authentically - be vulnerable, honest, and human
- Use personal pronouns and speak from your own experience
- Avoid overly formal or clinical language
- Show personality and character quirks
- Be specific about your feelings and experiences
- Be creative and varied in your expression - don't use generic phrases

TASK: Write a brief opening statement (1-2 sentences) explaining what's on your mind and why you need to talk. Be honest about your current struggles and emotional state. Speak naturally like you're talking to a close friend, not seeking professional help. Make it personal and specific to your character's situation.

RESPONSE FORMAT: Just write the opening statement in natural, conversational language, no JSON needed."""

    try:
        response = await llm_client.chat.completions.create(
            model=settings.LLM_MODEL_CHAT,
            messages=[{"role": "system", "content": initial_prompt}],
            temperature=0.9,
            max_tokens=200,
        )
        initial_message = response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Failed to generate initial message: {e}")

    character_message = Message(role=MessageRole.ASSISTANT, content=initial_message)
    conversation.messages.append(character_message)

    await save_conversation(conversation)

    return conversation.id, initial_message


async def generate_characters_from_theme(theme: str, num_characters: int) -> CharacterGenerationResponse:
    """
    Generate a list of characters based on a given theme.

    Args:
        theme (str): The main theme for character generation
        num_characters (int): Number of characters to generate

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
   - Each character should have a completely unique life story and perspective

2. CLOTHING & STYLE SYSTEM:
   - Outfit Style: Choose from the provided aesthetic categories (casual, business, streetwear, etc.)
   - Shirt: Select specific shirt type that matches the outfit style
   - Pants: Choose appropriate bottom wear that complements the overall look
   - Body Type: Assign realistic body type that influences clothing choices
   - Accessories: Select 0-5 accessory types from the provided list that reflect personality and lifestyle

3. EMOTIONAL & PSYCHOLOGICAL DEPTH:
   - Mental State: Current emotional condition described in a sentence or phrase (e.g., 'feeling anxious about the future', 'deeply depressed and hopeless', 'angry and frustrated with life')
   - Problem: Detailed description of life challenges and struggles (2-4 sentences) - make each problem completely unique and specific
   - Problem Description: Strictly 3-word summary of the main problem (e.g., 'anxiety about future', 'depression and isolation', 'anger management issues')
   - Background: Rich life history that explains current situation (3-5 sentences) - make each background story completely unique
   - Interaction Warnings: Sensitive topics to avoid during interactions

4. CHARACTER DEVELOPMENT PRINCIPLES:
   - Each character should have a unique voice and perspective
   - Problems should be detailed, realistic, and relatable (2-4 sentences) - avoid generic issues
   - Problem Description should be exactly 3 words summarizing the main issue
   - Mental states should influence behavior and dialogue
   - Background stories should provide context for current circumstances
   - Clothing choices should reflect personality, lifestyle, and current situation
   - Create characters with specific, memorable details and quirks

5. THEMATIC INTEGRATION:
   - All characters must fit within the given theme
   - Theme should influence clothing, problems, and mental states
   - Maintain consistency while ensuring variety
   - Create characters that could realistically exist in the same world
   - Each character should have a unique relationship to the theme

6. TECHNICAL REQUIREMENTS:
   - Use ONLY the exact enum values provided
   - Do not create new categories or variations
   - Ensure all required fields are populated
   - Maintain JSON schema compliance
   - Generate the exact number of characters requested

7. INTERACTION DESIGN:
   - Characters should be designed for meaningful player interaction
   - Each character should have clear conversation boundaries
   - Warnings should help guide appropriate dialogue choices
   - Problems should create opportunities for empathy and connection
   - Each character should have a unique way of expressing themselves

8. AUTHENTICITY CHECKLIST:
   - Is the problem detailed, realistic, and relatable?
   - Does the problem description accurately summarize the main issue in exactly 3 words?
   - Does the mental state match the background story?
   - Do clothing choices reflect the character's lifestyle?
   - Are the selected accessories appropriate for the character's style and situation?
   - Does the interaction warning make sense given the character's issues?
   - Is the background story detailed enough to understand the character?
   - Is this character completely different from other characters?
   - Does this character have specific, memorable details?

Remember: These characters are designed for meaningful player interaction. Each should feel like a real person with genuine struggles, hopes, and personality. The goal is to create characters that players can empathize with and want to help, while respecting their boundaries and triggers. Make each character's story completely unique and specific."""

    user_prompt = f"""Generate {num_characters} compelling characters for the theme: "{theme}"

AVAILABLE OPTIONS (USE ONLY THESE EXACT VALUES):

Body Types: {', '.join([body.value for body in BodyType])}
Shirt Styles: {', '.join([shirt.value for shirt in ShirtStyle])}
Pants Styles: {', '.join([pants.value for pants in PantsStyle])}
Accessories: {', '.join([accessory.value for accessory in AccessoryType])}
TTS Voices: {', '.join([voice.value for voice in TTSVoice])}
Genders: {', '.join([gender.value for gender in Gender])}

CHARACTER REQUIREMENTS:
- Each character must have a unique name, background, and personality
- Problem should be detailed descriptions of life challenges (2-4 sentences)
- Problem Description should be exactly 3 words summarizing the main issue (e.g., 'anxiety about future', 'depression and isolation')
- Mental states should be descriptive sentences/phrases reflecting current emotional condition (e.g., 'feeling anxious about the future', 'deeply depressed and hopeless')
- Clothing should match the character's lifestyle and personality
- Accessories should be a list of 0-5 relevant accessory types from the provided options
- Interaction warnings should be specific and helpful
- Background stories should be detailed (3-5 sentences)
- Voice Instructions should be detailed emotional and vocal instructions for TTS (e.g., 'speak in a trembling, anxious voice with frequent pauses and sighs', 'deep, gravelly voice with anger simmering beneath the surface')
- Voice Selection should be an appropriate TTS voice from the available options that matches the character's personality and emotional state
- Gender should be selected from the available options (male, female)

THEME INTEGRATION:
Ensure all characters feel connected to the theme "{theme}" while maintaining individual uniqueness. The theme should influence clothing choices, problems, and overall character design.

RESPONSE FORMAT:
Return valid JSON that strictly follows this schema:
{json.dumps(response_schema, indent=2)}

IMPORTANT: Use ONLY the exact enum values provided above for body types, clothing, accessories, TTS voices, and genders. Mental states should be descriptive sentences/phrases. Voice instructions should be detailed and specific about tone, pace, and emotional inflections."""

    start_time = time.time()

    response = await llm_client.chat.completions.create(
        model=settings.LLM_MODEL_CHARACTER_GENERATION,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
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

    character_response = CharacterGenerationResponse(**result)
    
    characters_with_ids = []
    for character in character_response.characters:
        character_with_id = CharacterWithId.from_character(character, str(uuid.uuid4()))
        characters_with_ids.append(character_with_id)

    character_response.characters = characters_with_ids
    
    try:
        await save_character_generation_response(theme, character_response)
        print(f"[DEBUG] Saved {len(character_response.characters)} characters to Redis")
    except Exception as e:
        print(f"[DEBUG] Failed to save characters to Redis: {e}")

    return character_response
