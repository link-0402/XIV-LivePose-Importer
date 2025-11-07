# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "XIV LivePose Importer",
    "author": "Luci",
    "description": "Import and apply FFXIV LivePose files to Blender armatures & animations",
    "blender": (4, 0, 0),
    "version": (1, 0, 0),
    "location": "View3D > Sidebar > LivePose Tab",
    "category": "Rigging"
}

import bpy
import json
import mathutils
import os
from bpy.props import StringProperty, PointerProperty, EnumProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


def update_target_armature(self, context):
    """Callback when target armature is changed"""
    if self.target_armature and "Mannequin" in bpy.data.objects:
        mannequin = bpy.data.objects["Mannequin"]
        
        # Find or create armature modifier on Mannequin
        armature_mod = None
        for mod in mannequin.modifiers:
            if mod.type == 'ARMATURE':
                armature_mod = mod
                break
        
        # Create armature modifier if it doesn't exist
        if not armature_mod:
            armature_mod = mannequin.modifiers.new(name="Armature", type='ARMATURE')
        
        # Set the armature object
        armature_mod.object = self.target_armature


class LivePoseSettings(bpy.types.PropertyGroup):
    target_armature: PointerProperty(
        name='Target Armature',
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE',
        update=update_target_armature
    ) # type: ignore
    
    livepose_filepath: StringProperty(
        name="LivePose File",
        description="Path to the .livepose file",
        default="",
        subtype='FILE_PATH'
    ) # type: ignore
    
    apply_mode: EnumProperty(
        name="Apply Mode",
        description="What transformations to apply from the LivePose file",
        items=[
            ('ALL', "All", "Apply position, rotation, and scale"),
            ('ROTATION', "Rotation Only", "Apply only rotations"),
            ('POSITION', "Position Only", "Apply only positions"),
            ('SCALE', "Scale Only", "Apply only scale"),
            ('ROT_POS', "Rotation + Position", "Apply rotation and position"),
        ],
        default='ROTATION'
    ) # type: ignore
    
    apply_to_animation: bpy.props.BoolProperty(
        name="Apply to Animation",
        description="Apply LivePose offset to all keyframes in the active action",
        default=True
    ) # type: ignore
    
    invert_transform: bpy.props.BoolProperty(
        name="Invert (Remove)",
        description="Apply the inverse transformation to undo a previously applied LivePose",
        default=False
    ) # type: ignore
    
    gltf_export_path: StringProperty(
        name="Export Path",
        description="Path where the GLTF file will be exported",
        default="",
        subtype='DIR_PATH'
    ) # type: ignore
    
    gltf_export_filename: StringProperty(
        name="Export Filename",
        description="Filename for the exported GLTF file (without extension)",
        default="export"
    ) # type: ignore
    
    pose_was_applied: bpy.props.BoolProperty(default=False) # type: ignore


class LIVEPOSE_PT_MainPanel(bpy.types.Panel):
    bl_label = "LivePose Importer"
    bl_idname = "LIVEPOSE_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LivePose"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        settings = context.scene.livepose_settings

        # Target Armature
        box = layout.box()
        box.label(text='Target Armature:', icon='ARMATURE_DATA')
        box.prop(settings, "target_armature", text="")

        # LivePose File Selection
        box = layout.box()
        box.label(text='LivePose File:', icon='FILE')
        box.prop(settings, "livepose_filepath", text="")

        # Apply Mode
        box = layout.box()
        box.label(text='Apply Mode:', icon='MODIFIER')
        box.prop(settings, "apply_mode", text="")
        box.prop(settings, "apply_to_animation", text="Apply to Animation")
        box.prop(settings, "invert_transform", text="Invert (Remove)")

        # Action Buttons
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("livepose.apply_pose", text="Apply LivePose", icon="POSE_HLT")
        
        row = layout.row()
        row.operator("livepose.reset_pose", text="Reset Armature", icon="LOOP_BACK")

        # Info
        if settings.pose_was_applied:
            layout.separator()
            box = layout.box()
            box.label(text="Pose has been applied", icon="CHECKMARK")
        
        # Action Management
        layout.separator()
        box = layout.box()
        box.label(text='Action Management:', icon='ACTION')
        
        row = box.row()
        row.operator("livepose.delete_other_actions", text="Delete Other Actions", icon="TRASH")
        
        row = box.row()
        row.operator("livepose.delete_all_actions", text="Delete All Actions", icon="CANCEL")
        
        # GLTF Import/Export
        layout.separator()
        box = layout.box()
        box.label(text='GLTF Import/Export:', icon='IMPORT')
        
        row = box.row()
        row.operator("livepose.import_gltf", text="Import GLTF", icon="IMPORT")
        
        box.prop(settings, "gltf_export_path", text="Export Folder")
        box.prop(settings, "gltf_export_filename", text="Filename")
        row = box.row()
        row.operator("livepose.export_gltf", text="Export GLTF", icon="EXPORT")
        row = box.row()
        row.operator("livepose.export_gltf", text="Export GLTF", icon="EXPORT")


class LIVEPOSE_OT_ApplyPose(bpy.types.Operator):
    bl_idname = "livepose.apply_pose"
    bl_label = "Apply LivePose"
    bl_description = "Apply the LivePose data to the target armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        settings = context.scene.livepose_settings
        if not settings.target_armature:
            return False
        if not settings.livepose_filepath:
            return False
        return True

    def execute(self, context):
        settings = context.scene.livepose_settings
        
        # Validate inputs
        if not os.path.exists(settings.livepose_filepath):
            self.report({'ERROR'}, f"LivePose file not found: {settings.livepose_filepath}")
            return {'CANCELLED'}
        
        # Load and parse LivePose file
        try:
            with open(settings.livepose_filepath, 'r') as f:
                livepose_data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load LivePose file: {str(e)}")
            return {'CANCELLED'}
        
        # Validate LivePose structure
        if 'Data' not in livepose_data:
            self.report({'ERROR'}, "Invalid LivePose file: missing 'Data' field")
            return {'CANCELLED'}
        
        target_armature = settings.target_armature
        
        # Check if applying to animation
        if settings.apply_to_animation:
            if not target_armature.animation_data or not target_armature.animation_data.action:
                self.report({'ERROR'}, "No active action found on armature. Please select an animation action first.")
                return {'CANCELLED'}
            
            return self.apply_to_animation_action(context, livepose_data, target_armature)
        else:
            return self.apply_to_current_pose(context, livepose_data, target_armature)
    
    def apply_to_current_pose(self, context, livepose_data, target_armature):
        """Apply LivePose to the current pose only"""
        settings = context.scene.livepose_settings
        applied_count = 0
        skipped_bones = []
        
        # DEBUG: Print first few bones for diagnostics
        print("\n=== LivePose Application Debug ===")
        
        for bone_data in livepose_data['Data']:
            if 'BonePoseInfoId' not in bone_data or 'Stacks' not in bone_data:
                continue
            
            bone_name = bone_data['BonePoseInfoId']['BoneName']
            
            if bone_name not in target_armature.pose.bones:
                skipped_bones.append(bone_name)
                continue
            
            posebone = target_armature.pose.bones[bone_name]
            
            for stack in bone_data['Stacks']:
                if 'Transform' not in stack:
                    continue
                
                # DEBUG: Print rotation data for first few bones
                if applied_count < 3 and 'Rotation' in stack['Transform']:
                    rot = stack['Transform']['Rotation']
                    print(f"\nBone: {bone_name}")
                    print(f"  LivePose Quat (XYZW): X={rot['X']:.6f}, Y={rot['Y']:.6f}, Z={rot['Z']:.6f}, W={rot['W']:.6f}")
                    print(f"  Current Blender Quat (WXYZ): {posebone.rotation_quaternion}")
                
                self.apply_transform_to_bone(posebone, stack['Transform'], settings.apply_mode, settings.invert_transform)
                
                # DEBUG: Print result
                if applied_count < 3 and 'Rotation' in stack['Transform']:
                    print(f"  After Apply: {posebone.rotation_quaternion}")
                
                applied_count += 1
        
        print("=== End Debug ===\n")
        
        if skipped_bones:
            self.report({'WARNING'}, f"Applied pose to {applied_count} bones. Skipped {len(skipped_bones)} missing bones: {', '.join(skipped_bones[:5])}{'...' if len(skipped_bones) > 5 else ''}")
        else:
            action_text = "Removed" if settings.invert_transform else "Applied"
            self.report({'INFO'}, f"Successfully {action_text.lower()} pose to {applied_count} bones")
        
        settings.pose_was_applied = True
        return {'FINISHED'}
    
    def apply_to_animation_action(self, context, livepose_data, target_armature):
        """Apply LivePose offset to all keyframes in the active action"""
        settings = context.scene.livepose_settings
        action = target_armature.animation_data.action
        
        # Build a dict of bone transforms from LivePose
        bone_transforms = {}
        for bone_data in livepose_data['Data']:
            if 'BonePoseInfoId' not in bone_data or 'Stacks' not in bone_data:
                continue
            
            bone_name = bone_data['BonePoseInfoId']['BoneName']
            if bone_name not in target_armature.pose.bones:
                continue
            
            for stack in bone_data['Stacks']:
                if 'Transform' in stack:
                    bone_transforms[bone_name] = stack['Transform']
                    break
        
        if not bone_transforms:
            self.report({'WARNING'}, "No matching bones found in LivePose data")
            return {'CANCELLED'}
        
        # Get all unique keyframes from ALL fcurves in the action
        frame_numbers = set()
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                frame_numbers.add(int(keyframe.co[0]))
        
        if not frame_numbers:
            self.report({'WARNING'}, "No keyframes found in action")
            return {'CANCELLED'}
        
        frame_numbers = sorted(frame_numbers)
        original_frame = context.scene.frame_current
        modified_bones = set()
        
        self.report({'INFO'}, f"Processing {len(frame_numbers)} frames from {min(frame_numbers)} to {max(frame_numbers)}")
        
        # Process each frame individually
        for frame in frame_numbers:
            # Set to the exact frame to ensure we're reading the correct keyframe values
            context.scene.frame_set(frame)
            # Force update to ensure pose is evaluated
            context.view_layer.update()
            
            for bone_name, transform in bone_transforms.items():
                posebone = target_armature.pose.bones[bone_name]
                
                # Store original values before applying transform
                original_loc = posebone.location.copy()
                original_rot = posebone.rotation_quaternion.copy()
                original_scale = posebone.scale.copy()
                
                # Apply the transform offset
                self.apply_transform_to_bone(posebone, transform, settings.apply_mode, settings.invert_transform)
                
                # Insert keyframe to bake the offset (only if values changed)
                if settings.apply_mode in ['ALL', 'POSITION', 'ROT_POS']:
                    if posebone.location != original_loc:
                        posebone.keyframe_insert(data_path="location", frame=frame)
                if settings.apply_mode in ['ALL', 'ROTATION', 'ROT_POS']:
                    posebone.rotation_mode = 'QUATERNION'
                    if posebone.rotation_quaternion != original_rot:
                        posebone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                if settings.apply_mode in ['ALL', 'SCALE']:
                    if posebone.scale != original_scale:
                        posebone.keyframe_insert(data_path="scale", frame=frame)
                
                modified_bones.add(bone_name)
        
        # Restore original frame
        context.scene.frame_set(original_frame)
        context.view_layer.update()
        
        action_text = "Removed" if settings.invert_transform else "Applied"
        self.report({'INFO'}, f"{action_text} LivePose offset to {len(modified_bones)} bones across {len(frame_numbers)} keyframes")
        settings.pose_was_applied = True
        return {'FINISHED'}
    
    def apply_transform_to_bone(self, posebone, transform, apply_mode, invert=False):
        """Apply a transform to a pose bone"""
        # Invert multiplier for remove operation
        mult = -1.0 if invert else 1.0
        
        # Apply Position
        if apply_mode in ['ALL', 'POSITION', 'ROT_POS'] and 'Position' in transform:
            pos = transform['Position']
            offset = mathutils.Vector((pos['X'], pos['Y'], pos['Z'])) * mult
            posebone.location += offset
        
        # Apply Rotation (quaternion)
        if apply_mode in ['ALL', 'ROTATION', 'ROT_POS'] and 'Rotation' in transform:
            rot = transform['Rotation']
            # Skip identity rotations
            if not (rot.get('IsIdentity', False)):
                posebone.rotation_mode = 'QUATERNION'
                # LivePose stores quaternions as XYZW, Blender uses WXYZ
                rot_quat = mathutils.Quaternion((
                    rot['W'], rot['X'], rot['Y'], rot['Z']
                ))
                
                # Normalize to ensure unit quaternion
                rot_quat.normalize()
                
                if invert:
                    # Apply inverse (conjugate) rotation for removal
                    rot_quat.conjugate()
                
                # Apply rotation using post-multiply (current @ delta)
                # This is the correct order for FFXIV LivePose data
                posebone.rotation_quaternion @= rot_quat
        
        # Apply Scale
        if apply_mode in ['ALL', 'SCALE'] and 'Scale' in transform:
            scale = transform['Scale']
            offset = mathutils.Vector((scale['X'], scale['Y'], scale['Z'])) * mult
            posebone.scale += offset


class LIVEPOSE_OT_ResetPose(bpy.types.Operator):
    bl_idname = "livepose.reset_pose"
    bl_label = "Reset Pose"
    bl_description = "Reset the armature to default pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        settings = context.scene.livepose_settings
        if not settings.target_armature:
            return False
        return True

    def execute(self, context):
        settings = context.scene.livepose_settings
        target_armature = settings.target_armature
        
        # Reset all pose bones to default
        for posebone in target_armature.pose.bones:
            posebone.location = mathutils.Vector((0.0, 0.0, 0.0))
            posebone.rotation_quaternion = mathutils.Quaternion((1.0, 0.0, 0.0, 0.0))
            posebone.rotation_euler = mathutils.Euler((0.0, 0.0, 0.0), 'XYZ')
            posebone.scale = mathutils.Vector((1.0, 1.0, 1.0))
        
        settings.pose_was_applied = False
        self.report({'INFO'}, "Armature pose reset to default")
        return {'FINISHED'}


class LIVEPOSE_OT_ImportGLTF(bpy.types.Operator, ImportHelper):
    bl_idname = "livepose.import_gltf"
    bl_label = "Import GLTF"
    bl_description = "Import a GLTF file and clean up unnecessary objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob: StringProperty(
        default="*.gltf;*.glb",
        options={'HIDDEN'}
    ) # type: ignore

    def execute(self, context):
        # Import GLTF with default settings
        try:
            bpy.ops.import_scene.gltf(filepath=self.filepath)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import GLTF: {str(e)}")
            return {'CANCELLED'}
        
        # Cleanup: Remove glTF_not_exported collection
        if "glTF_not_exported" in bpy.data.collections:
            collection = bpy.data.collections["glTF_not_exported"]
            
            # Remove all objects in the collection
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # Remove the collection itself
            bpy.data.collections.remove(collection)
            self.report({'INFO'}, "Removed glTF_not_exported collection")
        
        # Cleanup: Remove Icosphere object if it exists
        if "Icosphere" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["Icosphere"], do_unlink=True)
            self.report({'INFO'}, "Removed Icosphere object")
        
        # Cleanup: Remove DUMMY_MESH from Armature
        if "Armature" in bpy.data.objects:
            armature = bpy.data.objects["Armature"]
            # Look for DUMMY_MESH in children or as mesh
            for child in armature.children:
                if "DUMMY_MESH" in child.name:
                    bpy.data.objects.remove(child, do_unlink=True)
                    self.report({'INFO'}, "Removed DUMMY_MESH from Armature")
                    break
            
            # Also check if DUMMY_MESH exists as standalone object
            if "DUMMY_MESH" in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects["DUMMY_MESH"], do_unlink=True)
                self.report({'INFO'}, "Removed DUMMY_MESH object")
            
            # Set as target armature
            context.scene.livepose_settings.target_armature = armature
        
        self.report({'INFO'}, f"Successfully imported and cleaned GLTF: {os.path.basename(self.filepath)}")
        return {'FINISHED'}


class LIVEPOSE_OT_ExportGLTF(bpy.types.Operator):
    bl_idname = "livepose.export_gltf"
    bl_label = "Export GLTF"
    bl_description = "Export the target armature to GLTF with optimized settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.livepose_settings
        if not settings.target_armature:
            return False
        if not settings.gltf_export_path or not settings.gltf_export_filename:
            return False
        return True

    def execute(self, context):
        settings = context.scene.livepose_settings
        target_armature = settings.target_armature
        
        if not target_armature:
            self.report({'ERROR'}, "No target armature selected")
            return {'CANCELLED'}
        
        if not settings.gltf_export_path:
            self.report({'ERROR'}, "No export folder specified")
            return {'CANCELLED'}
        
        if not settings.gltf_export_filename:
            self.report({'ERROR'}, "No export filename specified")
            return {'CANCELLED'}
        
        # Build full file path
        export_folder = bpy.path.abspath(settings.gltf_export_path)
        filename = settings.gltf_export_filename
        if not filename.endswith('.gltf'):
            filename += '.gltf'
        filepath = os.path.join(export_folder, filename)
        
        # Ensure directory exists
        os.makedirs(export_folder, exist_ok=True)
        
        # Switch to Object mode if not already (export fails in Pose mode)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select target armature and its children
        target_armature.select_set(True)
        for child in target_armature.children:
            child.select_set(True)
        
        # Export GLTF with optimized settings for speed
        try:
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                use_selection=True,  # Limit to selected objects (target armature)
                export_format='GLTF_SEPARATE',  # GLTF_SEPARATE is faster than GLB for large files
                export_yup=True,  # + Y Up
                export_extras=True,  # Export custom properties as extras
                
                # Animation settings
                export_animations=True,
                export_anim_single_armature=False,
                export_nla_strips=False,
                export_reset_pose_bones=True,  # Reset Pose Bones between Actions
                export_optimize_animation_size=True,  # Optimize Animation Size
                export_anim_slide_to_zero=False,
                
                # Performance optimizations - disable unnecessary features
                export_cameras=False,  # Don't export cameras
                export_lights=False,  # Don't export lights
                export_apply=False,  # Don't apply modifiers (faster)
                export_texcoords=True,  # Keep UVs
                export_normals=True,  # Keep normals
                export_tangents=False,  # Skip tangents if not needed (faster)
                export_materials='EXPORT',  # Export materials
                
                # Texture/image optimization
                export_image_format='AUTO',  # Auto-detect format
                
                # Compression (can speed up for large files)
                export_draco_mesh_compression_enable=False,  # Draco compression is slow, keep disabled
            )
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export GLTF: {str(e)}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Successfully exported GLTF: {filename}")
        return {'FINISHED'}



class LIVEPOSE_OT_DeleteOtherActions(bpy.types.Operator):
    bl_idname = "livepose.delete_other_actions"
    bl_label = "Delete Other Actions"
    bl_description = "Delete all actions except the currently selected one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.livepose_settings
        if not settings.target_armature:
            return False
        if not settings.target_armature.animation_data:
            return False
        if not settings.target_armature.animation_data.action:
            return False
        return True

    def execute(self, context):
        settings = context.scene.livepose_settings
        target_armature = settings.target_armature
        
        if not target_armature.animation_data or not target_armature.animation_data.action:
            self.report({'ERROR'}, "No active action to preserve")
            return {'CANCELLED'}
        
        current_action = target_armature.animation_data.action
        deleted_count = 0
        
        # Collect all actions to delete (can't modify while iterating)
        actions_to_delete = []
        for action in bpy.data.actions:
            if action != current_action:
                actions_to_delete.append(action)
        
        # Delete all actions except current
        for action in actions_to_delete:
            bpy.data.actions.remove(action)
            deleted_count += 1
        
        self.report({'INFO'}, f"Deleted {deleted_count} actions. Kept: '{current_action.name}'")
        return {'FINISHED'}


class LIVEPOSE_OT_DeleteAllActions(bpy.types.Operator):
    bl_idname = "livepose.delete_all_actions"
    bl_label = "Delete All Actions"
    bl_description = "Delete all actions including the currently selected one"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Only enable if there are any actions to delete
        return len(bpy.data.actions) > 0

    def execute(self, context):
        settings = context.scene.livepose_settings
        deleted_count = len(bpy.data.actions)
        
        # Unlink action from armature first
        if settings.target_armature and settings.target_armature.animation_data:
            settings.target_armature.animation_data.action = None
        
        # Delete all actions
        actions_to_delete = list(bpy.data.actions)
        for action in actions_to_delete:
            bpy.data.actions.remove(action)
        
        self.report({'INFO'}, f"Deleted all {deleted_count} actions")
        return {'FINISHED'}


# Registration
classes = (
    LivePoseSettings,
    LIVEPOSE_PT_MainPanel,
    LIVEPOSE_OT_ApplyPose,
    LIVEPOSE_OT_ResetPose,
    LIVEPOSE_OT_ImportGLTF,
    LIVEPOSE_OT_ExportGLTF,
    LIVEPOSE_OT_DeleteOtherActions,
    LIVEPOSE_OT_DeleteAllActions,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.livepose_settings = PointerProperty(type=LivePoseSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.livepose_settings


if __name__ == "__main__":
    register()
