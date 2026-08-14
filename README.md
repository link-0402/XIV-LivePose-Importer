# XIV LivePoser - Blender Addon

Get the latest release here: https://github.com/link-0402/XIV-LivePose-Importer/releases/tag/1.2

A Blender addon for importing and applying FFXIV LivePose files to armatures, enabling easy pose adjustments for animations created in-game.
This tool is meant to be used primarily for permanent, simple animation editing rather than the semi-temporary animation-unspecific method that SimpleHeels already provides through livepose. 

I am in no way associated with the developers behind SimpleHeels, this is just a simple utility initially created for myself which I've wanted to share.

## Features

- **Import LivePose Files**: Load `.livepose` JSON files and apply them to Blender armatures
- **Multiple Apply Modes**: Choose what transformations to apply:
  - All transformations (position, rotation, scale)
  - Rotation only
  - Position only
  - Rotation + Position
- **Animation Support**: Apply LivePose offsets to entire animation actions across all keyframes, optionally only for select bones
- **Current Pose Support**: Turn off "Apply to Animation" to only modify the current pose instead of baking into an action
- **Invert (Remove)**: Apply the exact inverse of a LivePose to undo a previously applied pose
- **Per-Bone Toggles**: Enable or disable individual bones from the LivePose file, with "All" / "None" quick-toggle buttons; bones are displayed with human-readable English names
- **GLTF Import/Export**: Streamlined workflow with automatic cleanup of unnecessary objects; the scene frame range is set automatically from the imported animation
- **Action Management**: Delete individual or all animation actions (to reset the scene or make identifying the correct timeline on re-import ingame easier)
- **Automatic Armature Setup**: Automatically configures "Mannequin", "Face" and "Tail" meshes with armature modifier on import
- **CustomizePlus (C+) Integration**: Paste a CustomizePlus string to apply its bone scaling to the armature; scale keyframes are cleared from the animation and the scaling is reset automatically before GLTF export
- **Reset Armature**: Reset the armature pose back to its default state
- **Animation normalization / cleanup**: Cleans up the timeline in case of misplaced keyframes, putting evenly spaced keyframes across the length of the animation in order to make them game compatible

## Requirements

- Blender 4.0.0 or higher (only tested with 4.5.3 LTS)
- FFXIV LivePose files (`.livepose` format) saved through the SimpleHeels plugin
- (optional) A scene with a Mannequin of your chosen body mod for preview. Make sure it's name is "Mannequin", then the script automatically assigns the armature on import.
- An animation, typically exported from the game in GLTF Format (see the PAP editor in VFXEdit or XAT)

## Installation

1. Download the addon files
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install` and select the downloaded zip archive
4. Enable the addon by checking the box next to "XIV LivePose Importer" (typically happens automatically)

## Usage

### Basic Workflow

0. Export the animation from the game through either XAT (no clue) or VFXEdit (PapEditor Tab -> load pap file -> Motion)
   You need to load up the correct skeleton for the animation now, otherwise there will be issues. 
   Figuring out which one is correct can be a bit of trial and error, I usually try the IVCS 0101 (Midlander M) or or YAS / YAS+NLFB 0201 (Midlander F) and 0801 (Miqo'te F) skeletons.
   Keep in mind that if you use a skeleton that's not for Midlander Male or Female, most Mannequins will deform unnaturally, but the animation itself might still be completely fine. This is only an issue with the preview in Blender and you can mostly ignore it. You'll get a feel for it as you go. 
   Export the animation.

2. **Select Target Armature**
   - In the 3D Viewport sidebar (press `N`), navigate to the "LivePose" tab
   - Import a GLTF file through the importer
   - Select your target armature from the dropdown (if it didn't happen automatically)
   - Set the armature under the armature modifier of your Mannequin if you want a preview (recommended). If the body is called "Mannequin" this will happen automatically

3. **Load LivePose File**
   - Click the folder icon to browse for your `.livepose` file
   - LivePose files are JSON format exported from FFXIV tools

4. **Choose Apply Mode**
   - Select which transformations to apply based on the adjustments you made in LivePose. This will ususally be rotations only, or position to adjust some props or change the base height through the root bone.
   - You can toggle off adjustments for certain bones contained within the livepose file from the list if necessary

5. **Apply the Pose**
   - Click "Apply LivePose" to apply transformations
   - I recommend inspecting the animation / timeline in Pose Mode afterwards. If it contains too many or incorrectly placed keyframes hit "Normalize Animation", that will correct the timeline and provide evenly spaced keyframes across the entire animation. 
   - Tick "Invert (Remove)" and click "Apply LivePose" again to undo a previously applied pose (or just hit Ctrl Z)
   - Export the animation and re-import it ingame

6. Import the pose back into the game. 
   If anything you didn't edit, like toes or genitalia deform unnaturally, you might need to add them to a bone exclusion list. See https://xivmodding.com/books/ff14-asset-reference-document/page/bone-list-and-bone-scaling-notes for the list of bones.
   This happens due to a skeleton mismatch, but should be fixed by automatically picking the correct skeleton in future versions of VFXEditor (sorry, XAT folks).
  
## Technical Details

### LivePose File Format

The addon expects `.livepose` files with the following structure:
```json
{
  "Data": [
    {
      "BonePoseInfoId": {
        "BoneName": "bone_name"
      },
      "Stacks": [
        {
          "Transform": {
            "Position": {"X": 0.0, "Y": 0.0, "Z": 0.0},
            "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0, "W": 1.0},
            "Scale": {"X": 1.0, "Y": 1.0, "Z": 1.0}
          }
        }
      ]
    }
  ]
}
```

### How transforms are applied (important)

In-game, SimpleHeels/LivePose applies each stack to the bone's **model-space**
transform (relative to the skeleton root), not the bone-local transform:

- `model.Position += stack.Position`
- `model.Rotation = model.Rotation * stack.Rotation` (post-multiplied)
- `model.Scale += stack.Scale`

Bones are processed parents-first and children follow their parent's change.

- GLTF files exported by XAT/VFXEdit store the game's raw bone-local
  transforms, so the addon converts between Blender's bone-space and the
  game's model-space per bone (including Blender's bone-direction correction).
- All stacks of a bone are composed in file order.
- The offset is baked at every whole frame of the animation (the glTF
  exporter samples whole frames), which requires the animation's keys to sit
  on whole frames - applying to an animation therefore also normalizes its
  keyframe positions (same as the "Normalize Animation" button).

For exact math the addon parses the source GLTF's bind pose (the path is
remembered when you import through the addon's "Import GLTF" button). If it
is unavailable, it falls back to the conventions of Blender's default glTF
import settings. If you import GLTFs manually, keep the importer's
**Bone Dir setting at its default ("Blender")** - the "Temperance"/"Fortune"
heuristics do not round-trip cleanly through Blender's glTF exporter even
without this addon.

### GLTF Export

The export button exports the target armature and its children as a separate
`.gltf` (Y-up, with custom properties as extras and the full action range, not
the scene playback range). It switches to Object mode and deselects everything
else first, resets any active CustomizePlus scaling, and disables slow options
such as Draco compression.

## Troubleshooting

**"No active action found" error:**
- Ensure your armature has an animation action selected
- Check Animation Data properties in the outliner

**Bones are skipped:**
- Bone names must match exactly between LivePose file and armature
- Check console output for list of skipped bones

**Export fails:**
- Ensure export folder path exists and is writable
- Addon will create directories if they don't exist

**The last frame of the animation is missing after re-import:**
- Caused by fractional keyframe positions in imported glTF animations
  (e.g. a key at 238.9998 instead of 239). Applying a LivePose to the
  animation normalizes the keys to whole frames automatically, and the
  "Normalize Animation" button does the same thing manually.

**Pose looks incorrect:**
Depending on the skeleton used for the inital creation of the animation as well as the skeleton you exported the animation with, the animation may not correct on your chosen armature (if you choose to have one in the scene for preview) there may be some bones breaking after re-import into the game  That has nothing to do with this addon but rather how XIV handles skeletons / animations. 
If the limbs look twisted, also check that the glTF was imported with Blender's default "Bone Dir" import setting (see "How transforms are applied" above).

## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.
