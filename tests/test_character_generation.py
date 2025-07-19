import asyncio
import json
import pytest
from app.core.llm import (
    generate_characters_from_theme,
    CharacterGenerationResponse,
    Outfit,
    LifeProblem,
    MentalState,
)


@pytest.mark.asyncio
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
                assert character.shirt, "Character must have a shirt description"
                assert (
                    character.interaction_warning
                ), "Character must have an interaction warning"

                assert character.outfit in Outfit, f"Invalid outfit: {character.outfit}"
                assert (
                    character.mental_state in MentalState
                ), f"Invalid mental state: {character.mental_state}"

                assert (
                    len(character.problems) > 0
                ), "Character must have at least one problem"
                for problem in character.problems:
                    assert problem in LifeProblem, f"Invalid problem: {problem}"

                print(f"  Outfit: {character.outfit.value}")
                print(f"  Shirt: {character.shirt}")
                print(f"  Mental State: {character.mental_state.value}")
                print(f"  Problems: {', '.join([p.value for p in character.problems])}")

                if any(
                    [
                        character.accessories.hat,
                        character.accessories.glasses,
                        character.accessories.jewelry,
                        character.accessories.bag,
                        character.accessories.other,
                    ]
                ):
                    print("  Accessories:")
                    if character.accessories.hat:
                        print(f"    - Hat: {character.accessories.hat}")
                    if character.accessories.glasses:
                        print(f"    - Glasses: {character.accessories.glasses}")
                    if character.accessories.jewelry:
                        print(f"    - Jewelry: {character.accessories.jewelry}")
                    if character.accessories.bag:
                        print(f"    - Bag: {character.accessories.bag}")
                    if character.accessories.other:
                        print(f"    - Other: {character.accessories.other}")

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

    print("\n✅ JSON schema validation passed")


async def main():
    """Run all tests."""

    print("🧪 Starting Character Generation Tests\n")

    await test_json_schema_format()

    await test_character_generation()

    print("\n\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
