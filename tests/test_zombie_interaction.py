#!/usr/bin/env python3
"""End-to-end test for the zombie interaction system using API endpoints"""

import pytest
import httpx
import os
from rich.console import Console
from rich.panel import Panel

console = Console()


class ZombieInteractionTestRunner:
    def __init__(self):
        self.characters = []
        self.test_results = []
        self.base_url = "http://localhost:8000"
        self.tts_counter = 0

    async def generate_test_characters(self, num_characters: int = 1, theme: str = "relationship issues"):
        """Generate characters for testing via API"""
        with console.status(
            f"[bold green]Generating {num_characters} test characters via API...", spinner="dots"
        ):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    console.print(f"[dim]Making request to: {self.base_url}/chat/characters/generate[/dim]")
                    console.print(f"[dim]Request data: {{'theme': '{theme}', 'num_characters': {num_characters}}}[/dim]")
                    
                    response = await client.post(
                        f"{self.base_url}/chat/characters/generate",
                        json={"theme": theme, "num_characters": num_characters}
                    )
                    
                    console.print(f"[dim]Response status: {response.status_code}[/dim]")
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.characters = data["characters"]
                        console.print(
                            f"[green]✅ Generated {len(self.characters)} characters via API[/green]"
                        )
                        return data
                    else:
                        error_text = response.text
                        console.print(f"[red]❌ Failed to generate characters: {response.status_code}[/red]")
                        console.print(f"[red]❌ Error response: {error_text}[/red]")
                        raise Exception(f"API error: {response.status_code} - {error_text}")
                        
            except Exception as e:
                console.print(f"[red]❌ Failed to generate characters: {str(e)}[/red]")
                console.print(f"[red]❌ Exception type: {type(e).__name__}[/red]")
                raise

    async def request_tts(self, text: str, character_id: str, cycle_number: int = 0):
        """Request TTS for the given text with character-specific voice settings"""
        self.tts_counter += 1
        
        # Create unique file path using current project path + tts folder
        current_dir = os.getcwd()
        tts_folder = os.path.join(current_dir, "tts_output")
        
        # Create tts folder if it doesn't exist
        os.makedirs(tts_folder, exist_ok=True)
        
        # Generate unique filename
        filename = f"zombie_response_{cycle_number}_{self.tts_counter}.wav"
        file_path = os.path.join(tts_folder, filename)
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                console.print(f"[dim]Making TTS request to: {self.base_url}/tts[/dim]")
                console.print(f"[dim]TTS request data: {{'text': '{text[:50]}...', 'character_id': '{character_id}', 'stored_file_path': '{file_path}'}}[/dim]")
                
                response = await client.post(
                    f"{self.base_url}/tts",
                    json={
                        "text": text,
                        "character_id": character_id,
                        "stored_file_path": file_path
                    }
                )
                
                console.print(f"[dim]TTS response status: {response.status_code}[/dim]")
                
                if response.status_code == 200:
                    console.print(f"[green]✅ TTS generated successfully: {file_path}[/green]")
                    return file_path
                else:
                    error_text = response.text
                    console.print(f"[red]❌ TTS failed: {response.status_code}[/red]")
                    console.print(f"[red]❌ TTS error response: {error_text}[/red]")
                    raise Exception(f"TTS API error: {response.status_code} - {error_text}")
                    
        except Exception as e:
            console.print(f"[red]❌ TTS request failed: {str(e)}[/red]")
            console.print(f"[red]❌ TTS exception type: {type(e).__name__}[/red]")
            raise

    async def test_zombie_interaction(self, character_id: str, audio_file_path: str):
        """Test zombie interaction endpoint"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                console.print(f"[dim]Making request to: {self.base_url}/zombie[/dim]")
                console.print(f"[dim]Request data: {{'audio_file_path': '{audio_file_path}', 'character_id': '{character_id}'}}[/dim]")
                
                response = await client.post(
                    f"{self.base_url}/zombie",
                    json={
                        "audio_file_path": audio_file_path,
                        "character_id": character_id
                    }
                )
                
                console.print(f"[dim]Response status: {response.status_code}[/dim]")
                
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"[dim]Response data keys: {list(data.keys())}[/dim]")
                    return data
                else:
                    error_text = response.text
                    console.print(f"[red]❌ Failed zombie interaction: {response.status_code}[/red]")
                    console.print(f"[red]❌ Error response: {error_text}[/red]")
                    raise Exception(f"API error: {response.status_code} - {error_text}")
                    
        except Exception as e:
            console.print(f"[red]❌ Failed zombie interaction: {str(e)}[/red]")
            console.print(f"[red]❌ Exception type: {type(e).__name__}[/red]")
            raise

    async def get_zombie_initial_message(self, character_id: str):
        """Get initial message from zombie without sending audio"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                console.print(f"[dim]Making request to: {self.base_url}/zombie[/dim]")
                console.print(f"[dim]Request data: {{'character_id': '{character_id}'}}[/dim]")
                
                response = await client.post(
                    f"{self.base_url}/zombie",
                    json={"character_id": character_id}
                )
                
                console.print(f"[dim]Response status: {response.status_code}[/dim]")
                
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"[dim]Response data keys: {list(data.keys())}[/dim]")
                    return data
                else:
                    error_text = response.text
                    console.print(f"[red]❌ Failed to get initial message: {response.status_code}[/red]")
                    console.print(f"[red]❌ Error response: {error_text}[/red]")
                    raise Exception(f"API error: {response.status_code} - {error_text}")
                    
        except Exception as e:
            console.print(f"[red]❌ Failed to get initial message: {str(e)}[/red]")
            console.print(f"[red]❌ Exception type: {type(e).__name__}[/red]")
            raise

    async def cleanup_all_data(self):
        """Clean up all data via API"""
        console.print(Panel("[bold red]Cleaning up all test data[/bold red]"))
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(f"{self.base_url}/chat/cleanup")
                
                if response.status_code == 200:
                    result = response.json()
                    console.print(f"[green]✅ Cleanup successful: {result['message']}[/green]")
                else:
                    console.print(f"[red]❌ Cleanup failed: {response.status_code}[/red]")
                    
        except Exception as e:
            console.print(f"[red]❌ Cleanup error: {str(e)}[/red]")


@pytest.mark.asyncio
async def test_zombie_interaction_e2e():
    """End-to-end test for the zombie interaction system"""
    print("\n\n")
    
    console.print(
        Panel(
            "[bold cyan]🧟 Zombie Interaction End-to-End Test[/bold cyan]\n"
            "[cyan]Testing character generation and single audio interaction[/cyan]",
            border_style="cyan",
        )
    )

    runner = ZombieInteractionTestRunner()

    # Step 1: Generate test character
    console.print("\n[bold cyan]Step 1: Generating Test Character[/bold cyan]")
    try:
        response = await runner.generate_test_characters(1, "relationship issues")
        
        # Display generated character
        character = response["characters"][0]
        console.print(
            Panel(
                f"[bold cyan]🧟 Test Character: {character['name']}[/bold cyan]\n"
                f"Mental State: {character['mental_state']}\n"
                f"Problem: {character['problem'][:100]}...\n"
                f"Problem Description: {character['problem_description']}\n"
                f"Voice Instructions: {character.get('voice_instructions', 'N/A')[:100]}...\n"
                f"Voice Selection: {character.get('voice_selection', 'N/A')}\n"
                f"Interaction Warning: {character['interaction_warning']}",
                border_style="cyan",
            )
        )
        
    except Exception as e:
        console.print(f"[red]❌ Character generation failed: {str(e)}[/red]")
        return

    # Step 2: Get initial message from zombie
    console.print("\n[bold cyan]Step 2: Getting Initial Message from Zombie[/bold cyan]")
    try:
        initial_result = await runner.get_zombie_initial_message(character["id"])
        
        console.print(
            Panel(
                f"[bold green]✅ Zombie Initial Message![/bold green]\n"
                f"Character Response: {initial_result['character_response']}\n"
                f"Emotional State: {initial_result['emotional_state']}/100",
                border_style="green",
            )
        )
        
        # Log the AI response
        console.print(f"[yellow]🤖 AI Response: {initial_result['character_response']}[/yellow]")
        
        # Request TTS for initial message
        console.print("\n[bold magenta]🎵 Requesting TTS for Initial Message[/bold magenta]")
        try:
            tts_file = await runner.request_tts(initial_result['character_response'], character["id"], 0)
            console.print(f"[magenta]🎵 TTS file created: {tts_file}[/magenta]")
        except Exception as e:
            console.print(f"[red]❌ TTS failed for initial message: {str(e)}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to get initial message: {str(e)}[/red]")
        return

    # Step 3: Test zombie interaction with audio file
    console.print("\n[bold cyan]Step 3: Testing Zombie Interaction with Audio[/bold cyan]")
    try:
        interaction_result = await runner.test_zombie_interaction(
            character["id"], 
            # "/Users/user/Downloads/Recording.wav"
            "/Users/user/Downloads/fuck_you.wav"
        )
        
        console.print(
            Panel(
                f"[bold green]✅ Zombie Interaction Successful![/bold green]\n"
                f"Transcription: {interaction_result['transcription']}\n"
                f"Character Response: {interaction_result['character_response']}\n"
                f"Emotional Change: {interaction_result['emotional_change']:+d}\n"
                f"Emotional State: {interaction_result['emotional_state']}/100\n"
                f"Session Ended: {interaction_result['session_ended']}",
                border_style="green",
            )
        )
        
        # Log the transcription and AI response
        console.print(f"[blue]🎤 Transcription: {interaction_result['transcription']}[/blue]")
        console.print(f"[yellow]🤖 AI Response: {interaction_result['character_response']}[/yellow]")
        
        # Request TTS for interaction response
        console.print("\n[bold magenta]🎵 Requesting TTS for Interaction Response[/bold magenta]")
        try:
            tts_file = await runner.request_tts(interaction_result['character_response'], character["id"], 1)
            console.print(f"[magenta]🎵 TTS file created: {tts_file}[/magenta]")
        except Exception as e:
            console.print(f"[red]❌ TTS failed for interaction response: {str(e)}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Zombie interaction failed: {str(e)}[/red]")
        return

    # Step 4: Cycle through same audio file until session ends
    console.print("\n[bold cyan]Step 4: Cycling Through Audio Until Session Ends[/bold cyan]")
    
    cycle_count = 0
    max_cycles = 10  # Prevent infinite loops
    
    while cycle_count < max_cycles:
        cycle_count += 1
        console.print(f"\n[cyan]🔄 Cycle {cycle_count}[/cyan]")
        
        try:
            cycle_result = await runner.test_zombie_interaction(
                character["id"], 
                # "/Users/user/Downloads/Recording.wav"
                "/Users/user/Downloads/fuck_you.wav"
            )
            
            # Log the transcription and AI response
            console.print(f"[blue]🎤 Transcription: {cycle_result['transcription']}[/blue]")
            console.print(f"[yellow]🤖 AI Response: {cycle_result['character_response']}[/yellow]")
            console.print(f"[green]Emotional State: {cycle_result['emotional_state']}/100 (Change: {cycle_result['emotional_change']:+d})[/green]")
            
            # Request TTS for cycle response
            console.print(f"\n[bold magenta]🎵 Requesting TTS for Cycle {cycle_count} Response[/bold magenta]")
            try:
                tts_file = await runner.request_tts(cycle_result['character_response'], character["id"], cycle_count)
                console.print(f"[magenta]🎵 TTS file created: {tts_file}[/magenta]")
            except Exception as e:
                console.print(f"[red]❌ TTS failed for cycle {cycle_count}: {str(e)}[/red]")
            
            if cycle_result['session_ended']:
                if cycle_result['emotional_state'] >= 100:
                    console.print("[bold green]🎉 Session ended - Character is satisfied![/bold green]")
                else:
                    console.print("[bold red]💥 Session ended - Character is enraged![/bold red]")
                break
                
        except Exception as e:
            console.print(f"[red]❌ Cycle {cycle_count} failed: {str(e)}[/red]")
            break
    
    if cycle_count >= max_cycles:
        console.print("[yellow]⚠️ Reached maximum cycles without session ending[/yellow]")

    # Step 5: Cleanup
    console.print("\n[bold cyan]Step 5: Cleanup[/bold cyan]")
    await runner.cleanup_all_data()

    console.print(
        Panel(
            "[bold green]✅ Zombie Interaction E2E Test Complete![/bold green]",
            border_style="green",
        )
    )


@pytest.mark.asyncio
async def test_zombie_interaction_error_cases():
    """Test error cases for zombie interaction"""
    console.print(
        Panel(
            "[bold red]🧟 Zombie Interaction Error Case Tests[/bold red]\n"
            "[red]Testing error handling for invalid inputs[/red]",
            border_style="red",
        )
    )

    runner = ZombieInteractionTestRunner()

    # Test 1: Invalid character ID
    console.print("\n[bold red]Test 1: Invalid Character ID[/bold red]")
    
    try:
        # result = await runner.test_zombie_interaction("invalid-uuid", "/Users/user/Downloads/Recording.wav")
        result = await runner.test_zombie_interaction("invalid-uuid", "/Users/user/Downloads/fuck_you.wav")
        console.print("[red]❌ Should have failed with invalid character ID[/red]")
    except Exception as e:
        console.print(f"[green]✅ Correctly failed with invalid character ID: {str(e)}[/green]")

    # Test 2: Non-existent audio file
    console.print("\n[bold red]Test 2: Non-existent Audio File[/bold red]")
    
    try:
        result = await runner.test_zombie_interaction("some-uuid", "/path/to/nonexistent/file.wav")
        console.print("[red]❌ Should have failed with non-existent file[/red]")
    except Exception as e:
        console.print(f"[green]✅ Correctly failed with non-existent file: {str(e)}[/green]")

    console.print(
        Panel(
            "[bold green]✅ Error Case Tests Complete![/bold green]",
            border_style="green",
        )
    ) 