import asyncio
import json
import pytest
from app.core.llm import (
    generate_characters_from_theme,
    CharacterGenerationResponse,
    ShirtStyle,
    PantsStyle,
    BodyType,
    AccessoryType,
)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_character_generation():
    """Test the character generation function with different themes."""

    print("Testing character generation...")

    themes = ["urban dystopia", "medieval fantasy tavern", "corporate burnout"]

    for theme in themes:
        print(f"\n{'='*60}")
        print(f"Testing theme: {theme}")
        print("=" * 60)

        try:
            response = await generate_characters_from_theme(theme)

            assert isinstance(
                response, CharacterGenerationResponse
            ), f"Expected CharacterGenerationResponse, got {type(response)}"

            assert (
                response.theme == theme
            ), f"Expected theme '{theme}', got '{response.theme}'"

            assert (
                len(response.characters) >= 3
            ), f"Expected at least 3 characters, got {len(response.characters)}"
            assert (
                len(response.characters) <= 5
            ), f"Expected at most 5 characters, got {len(response.characters)}"

            print(f"\n✅ Generated {len(response.characters)} characters for '{theme}'")

            for i, character in enumerate(response.characters):
                print(f"\n--- Character {i+1}: {character.name} ---")

                assert character.name, "Character must have a name"
                assert character.background, "Character must have a background"
                assert character.shirt, "Character must have a shirt"
                assert character.pants, "Character must have pants"
                assert character.body_type, "Character must have a body type"
                assert character.mental_state, "Character must have a mental state"
                assert (
                    character.interaction_warning
                ), "Character must have an interaction warning"

                # Enum validation
                assert (
                    character.shirt in ShirtStyle
                ), f"Invalid shirt: {character.shirt}"
                assert (
                    character.pants in PantsStyle
                ), f"Invalid pants: {character.pants}"
                assert (
                    character.body_type in BodyType
                ), f"Invalid body type: {character.body_type}"

                # Problems validation
                assert character.problems, "Character must have problems description"
                assert (
                    len(character.problems) >= 10
                ), "Problems description should be detailed (at least 10 characters)"

                assert isinstance(
                    character.accessories, list
                ), "Accessories must be a list"
                for accessory in character.accessories:
                    assert accessory in AccessoryType, f"Invalid accessory: {accessory}"

                print(f"  Shirt: {character.shirt.value}")
                print(f"  Pants: {character.pants.value}")
                print(f"  Body Type: {character.body_type.value}")
                print(f"  Mental State: {character.mental_state}")
                print(f"  Problems: {character.problems[:100]}...")

                if character.accessories:
                    print(
                        f"  Accessories: {', '.join([a.value for a in character.accessories])}"
                    )
                else:
                    print("  Accessories: None")

                print(f"  Warning: {character.interaction_warning}")

            json_str = response.model_dump_json(indent=2)
            print(f"\n📄 JSON output preview (first 500 chars):")
            print(json_str)

            parsed = json.loads(json_str)
            reconstructed = CharacterGenerationResponse(**parsed)
            assert len(reconstructed.characters) == len(
                response.characters
            ), "Serialization/deserialization failed"

            print(f"\n✅ All validations passed for theme: '{theme}'")

        except Exception as e:
            print(f"\n❌ Error testing theme '{theme}': {str(e)}")
            raise


@pytest.mark.asyncio
async def test_json_schema_format():
    """Test that the JSON schema is properly formatted."""

    print("\n" + "=" * 60)
    print("Testing JSON Schema Format")
    print("=" * 60)

    schema = CharacterGenerationResponse.model_json_schema()

    print("\nGenerated JSON Schema:")
    print(json.dumps(schema, indent=2))

    assert "properties" in schema, "Schema must have properties"
    assert "theme" in schema["properties"], "Schema must have theme property"
    assert "characters" in schema["properties"], "Schema must have characters property"

    character_schema = schema["properties"]["characters"]["items"]
    required_fields = [
        "name",
        "background",
        "shirt",
        "pants",
        "body_type",
        "accessories",
        "problems",
        "mental_state",
        "interaction_warning",
    ]

    if "properties" in character_schema:
        for field in required_fields:
            assert (
                field in character_schema["properties"]
            ), f"Character schema must have {field} property"
    else:
        assert (
            "$ref" in character_schema
        ), "Character schema must have properties or $ref"

    print("\n✅ JSON schema validation passed")


@pytest.mark.asyncio
async def test_enum_values():
    """Test that all enum values are properly defined."""

    print("\n" + "=" * 60)
    print("Testing Enum Values")
    print("=" * 60)

    # Test enum counts
    print(f"ShirtStyle options: {len(ShirtStyle)}")
    print(f"PantsStyle options: {len(PantsStyle)}")
    print(f"BodyType options: {len(BodyType)}")
    print(f"AccessoryType options: {len(AccessoryType)}")

    # Verify minimum counts
    assert len(ShirtStyle) >= 10, "Should have at least 10 shirt styles"
    assert len(PantsStyle) >= 10, "Should have at least 10 pants styles"
    assert len(BodyType) >= 5, "Should have at least 5 body types"
    assert len(AccessoryType) >= 10, "Should have at least 10 accessory types"

    print("\n✅ Enum validation passed")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_character_validation():
    """Test character validation with edge cases."""

    print("\n" + "=" * 60)
    print("Testing Character Validation")
    print("=" * 60)

    # Test a simple theme to ensure validation works
    try:
        response = await generate_characters_from_theme("test theme")

        for character in response.characters:
            # Test that problems description is detailed
            assert (
                len(character.problems) >= 10
            ), f"Problems description too short: {len(character.problems)} characters"

            # Test that accessories is a list
            assert isinstance(
                character.accessories, list
            ), "Accessories should be a list"

            # Test that all enum values are valid
            assert character.shirt in ShirtStyle
            assert character.pants in PantsStyle
            assert character.body_type in BodyType

            for accessory in character.accessories:
                assert accessory in AccessoryType

        print("✅ Character validation passed")

    except Exception as e:
        print(f"❌ Character validation failed: {str(e)}")
        raise


async def main():
    """Run all tests."""

    print("🧪 Starting Character Generation Tests\n")

    await test_json_schema_format()
    await test_enum_values()
    await test_character_validation()
    await test_character_generation()

    print("\n\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
