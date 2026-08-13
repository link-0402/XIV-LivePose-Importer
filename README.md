# XIV LivePoser - Blender Addon

Get the latest release here: https://github.com/link-0402/XIV-LivePose-Importer/releases/tag/1.0

A Blender addon for importing and applying FFXIV LivePose files to armatures, enabling easy pose adjustments for animations created in-game.
This tool is meant to be used primarily for permanent, simple animation editing rather than the semi-temporary animation-unspecific method that SimpleHeels already provides through livepose. 

I am in no way associated with the developers behind SimpleHeels, this is just a simple utility initially created for myself which I've wanted to share.

## Features

- **Import LivePose Files**: Load `.livepose` JSON files and apply them to Blender armatures
- **Multiple Apply Modes**: Choose what transformations to apply:
  - All transformations (position, rotation, scale)
  - Rotation only
  - Position only
  - Scale only
  - Rotation + Position
- **Animation Support**: Apply LivePose offsets to entire animation actions across all keyframes
- **Invert Transformations**: Remove previously applied LivePose data
- **GLTF Import/Export**: Streamlined workflow with automatic cleanup of unnecessary objects
- **Action Management**: Delete individual or all animation actions
- **Automatic Armature Setup**: Automatically configures Mannequin mesh with armature modifier

## Requirements

- Blender 4.0.0 or higher (only tested with 4.5.3 LTS)
- FFXIV LivePose files (`.livepose` format) saved through the SimpleHeels plugin
- (optional) A scene with a Mannequin of your chosen body mod for preview. Make sure it's name is "Mannequin", then the script automatically assigns the armature on import.
- An animation, typically exported from the game in GLTF Format (see the PAP editor in VFXEdit or XAT)

## Installation

1. Download the addon files
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install` and select the downloaded zip archive
4. Enable the addon by checking the box next to "Rigging: LivePose Importer" (typically happens automatically)

## Usage

### Basic Workflow

1. **Select Target Armature**
   - In the 3D Viewport sidebar (press `N`), navigate to the "LivePose" tab
   - Import a GLTF file through the importer
   - Select your target armature from the dropdown

2. **Load LivePose File**
   - Click the folder icon to browse for your `.livepose` file
   - LivePose files are JSON format exported from FFXIV tools

3. **Choose Apply Mode**
   - Select which transformations to apply (default: Rotation Only)
   - Toggle "Apply to Animation" to apply the pose across all keyframes
   - Toggle "Invert (Remove)" to undo a previously applied pose

4. **Apply the Pose**
   - Click "Apply LivePose" to apply transformations
   - Export the animation and re-import it ingame

### GLTF Workflow

**Import GLTF:**
- Click "Import GLTF" to import animation files
- The addon automatically removes unnecessary objects:
  - `glTF_not_exported` collection
  - `Icosphere` object
  - `DUMMY_MESH` object
- Automatically sets imported armature as target

**Export GLTF:**
- Set export folder path
- Enter filename (`.gltf` extension added automatically)
- Click "Export GLTF" to export with optimized settings
- Export includes animations with reset pose bones between actions

### Action Management

- **Delete Other Actions**: Removes all actions except the currently active one
- **Delete All Actions**: Removes all animation actions from the project

## Apply Modes Explained

- **All**: Applies position, rotation, and scale transformations
- **Rotation Only**: Only applies bone rotations (most common for poses)
- **Position Only**: Only applies bone location offsets
- **Scale Only**: Only applies bone scale transformations
- **Rotation + Position**: Applies both rotation and position (common for character poses)

## Animation Application

When "Apply to Animation" is enabled:
- LivePose transformations are applied to all keyframes in the active action
- Each frame is processed individually to preserve animation timing
- New keyframes are inserted only where values change
- Progress is reported showing number of bones and frames modified

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

Bones are processed parents-first and children follow their parent's change
(the usual `Propogate: 3` flag). This addon reproduces that behavior exactly:

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

## Credits

**Author**: Luci  
**Category**: Rigging  
**Version**: 1.0.0

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.
