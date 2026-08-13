# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import json
import math
import mathutils
import os
import struct
import base64
import zlib
from collections import defaultdict
from bpy.props import StringProperty, PointerProperty, EnumProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


# Bone name to English mapping dictionary
BONE_NAME_MAPPING = {
    # Main Bones
    'n_root': 'Root',
    'n_hara': 'Center of Mass/Belly',
    'n_throw': 'Throw Point',
    'j_kao': 'Head/Face',
    'j_kubi': 'Neck',
    'j_ago': 'Chin/Jaw (Pre-DT)',
    'j_kosi': 'Hip/Lower Back/Waist',
    
    # Spine
    'j_sebo_a': 'Spine A',
    'j_sebo_b': 'Spine B',
    'j_sebo_c': 'Spine C',
    
    # Arms
    'j_ude_a_l': 'Left Upper Arm',
    'j_ude_a_r': 'Right Upper Arm',
    'j_ude_b_l': 'Left Lower Arm',
    'j_ude_b_r': 'Right Lower Arm',
    'n_hhiji_l': 'Left Elbow',
    'n_hhiji_r': 'Right Elbow',
    'n_hte_l': 'Left Wrist',
    'n_hte_r': 'Right Wrist',
    'j_te_l': 'Left Hand',
    'j_te_r': 'Right Hand',
    'j_sako_l': 'Left Collar/Clavicle',
    'j_sako_r': 'Right Collar/Clavicle',
    'n_hkata_l': 'Left Shoulder',
    'n_hkata_r': 'Right Shoulder',
    
    # Breasts
    'j_mune_l': 'Left Breast',
    'j_mune_r': 'Right Breast',
    
    # Legs
    'j_asi_a_l': 'Left Upper Leg',
    'j_asi_a_r': 'Right Upper Leg',
    'j_asi_b_l': 'Left Mid Leg',
    'j_asi_b_r': 'Right Mid Leg',
    'j_asi_c_l': 'Left Lower Leg',
    'j_asi_c_r': 'Right Lower Leg',
    'j_asi_d_l': 'Left Foot',
    'j_asi_d_r': 'Right Foot',
    'j_asi_e_l': 'Left Toe',
    'j_asi_e_r': 'Right Toe',
    
    # Skirt
    'j_sk_f_a_l': 'Skirt Front A Left',
    'j_sk_f_a_r': 'Skirt Front A Right',
    'j_sk_f_b_l': 'Skirt Front B Left',
    'j_sk_f_b_r': 'Skirt Front B Right',
    'j_sk_f_c_l': 'Skirt Front C Left',
    'j_sk_f_c_r': 'Skirt Front C Right',
    'j_sk_b_a_l': 'Skirt Back A Left',
    'j_sk_b_a_r': 'Skirt Back A Right',
    'j_sk_b_b_l': 'Skirt Back B Left',
    'j_sk_b_b_r': 'Skirt Back B Right',
    'j_sk_b_c_l': 'Skirt Back C Left',
    'j_sk_b_c_r': 'Skirt Back C Right',
    'j_sk_s_a_l': 'Skirt Side A Left',
    'j_sk_s_a_r': 'Skirt Side A Right',
    'j_sk_s_b_l': 'Skirt Side B Left',
    'j_sk_s_b_r': 'Skirt Side B Right',
    'j_sk_s_c_l': 'Skirt Side C Left',
    'j_sk_s_c_r': 'Skirt Side C Right',
    
    # Hair
    'j_kami_a': 'Hair A (Ponytail)',
    'j_kami_b': 'Hair B (Ponytail)',
    'j_kami_f_l': 'Left Bangs',
    'j_kami_f_r': 'Right Bangs',
    
    # Ears
    'j_mimi_l': 'Left Ear',
    'j_mimi_r': 'Right Ear',
    
    # Viera Ears
    'j_zera_a_l': 'Left Viera Ear A Base',
    'j_zera_a_r': 'Right Viera Ear A Base',
    'j_zera_b_l': 'Left Viera Ear A Tip',
    'j_zera_b_r': 'Right Viera Ear A Tip',
    'j_zerb_a_l': 'Left Viera Ear B Base',
    'j_zerb_a_r': 'Right Viera Ear B Base',
    'j_zerb_b_l': 'Left Viera Ear B Tip',
    'j_zerb_b_r': 'Right Viera Ear B Tip',
    'j_zerc_a_l': 'Left Viera Ear C Base',
    'j_zerc_a_r': 'Right Viera Ear C Base',
    'j_zerc_b_l': 'Left Viera Ear C Tip',
    'j_zerc_b_r': 'Right Viera Ear C Tip',
    'j_zerd_a_l': 'Left Viera Ear D Base',
    'j_zerd_a_r': 'Right Viera Ear D Base',
    'j_zerd_b_l': 'Left Viera Ear D Tip',
    'j_zerd_b_r': 'Right Viera Ear D Tip',
    
    # Tail
    'n_sippo_a': 'Tail A',
    'n_sippo_b': 'Tail B',
    'n_sippo_c': 'Tail C',
    'n_sippo_d': 'Tail D',
    'n_sippo_e': 'Tail E',
    
    # Earrings
    'n_ear_a_l': 'Left Earring Attach',
    'n_ear_a_r': 'Right Earring Attach',
    'n_ear_b_l': 'Left Earring Hang',
    'n_ear_b_r': 'Right Earring Hang',
    
    # Gear Specific
    'n_kataarmor_l': 'Left Shoulder Pad',
    'n_kataarmor_r': 'Right Shoulder Pad',
    'n_hizasoubi_l': 'Left Knee Pad',
    'n_hizasoubi_r': 'Right Knee Pad',
    'n_hijisoubi_l': 'Left Elbow Pad',
    'n_hijisoubi_r': 'Right Elbow Pad',
    
    # Weapons
    'j_buki_kosi_l': 'Left Sheathed Weapon (Hip)',
    'j_buki_kosi_r': 'Right Sheathed Weapon (Hip)',
    'j_buki2_kosi_l': 'Left Sheathed Weapon (Hip2)',
    'j_buki2_kosi_r': 'Right Sheathed Weapon (Hip2)',
    'j_buki_sebo_l': 'Left Sheathed Weapon (Back)',
    'j_buki_sebo_r': 'Right Sheathed Weapon (Back)',
    'n_buki_l': 'Left Drawn Weapon',
    'n_buki_r': 'Right Drawn Weapon',
    'n_buki_tate_l': 'Left Drawn Shield',
    'n_buki_tate_r': 'Right Drawn Shield',
    
    # Fingers - Thumb
    'j_oya_a_l': 'Left Thumb A',
    'j_oya_a_r': 'Right Thumb A',
    'j_oya_b_l': 'Left Thumb B',
    'j_oya_b_r': 'Right Thumb B',
    
    # Fingers - Index
    'j_hito_a_l': 'Left Index Finger A',
    'j_hito_a_r': 'Right Index Finger A',
    'j_hito_b_l': 'Left Index Finger B',
    'j_hito_b_r': 'Right Index Finger B',
    
    # Fingers - Middle
    'j_naka_a_l': 'Left Middle Finger A',
    'j_naka_a_r': 'Right Middle Finger A',
    'j_naka_b_l': 'Left Middle Finger B',
    'j_naka_b_r': 'Right Middle Finger B',
    
    # Fingers - Ring
    'j_kusu_a_l': 'Left Ring Finger A',
    'j_kusu_a_r': 'Right Ring Finger A',
    'j_kusu_b_l': 'Left Ring Finger B',
    'j_kusu_b_r': 'Right Ring Finger B',
    
    # Fingers - Pinky
    'j_ko_a_l': 'Left Pinky A',
    'j_ko_a_r': 'Right Pinky A',
    'j_ko_b_l': 'Left Pinky B',
    'j_ko_b_r': 'Right Pinky B',
    
    # Dawntrail Face Bones - Mouth
    'j_f_umlip_01_l': 'Left Upper Outer Lip (Lipline)',
    'j_f_umlip_01_r': 'Right Upper Outer Lip (Lipline)',
    'j_f_umlip_02_l': 'Left Upper Outer Lip (Opening)',
    'j_f_umlip_02_r': 'Right Upper Outer Lip (Opening)',
    'j_f_ulip_01_l': 'Left Upper Center Lip (Lipline)',
    'j_f_ulip_01_r': 'Right Upper Center Lip (Lipline)',
    'j_f_ulip_02_l': 'Left Upper Center Lip (Opening)',
    'j_f_ulip_02_r': 'Right Upper Center Lip (Opening)',
    'j_f_uslip_l': 'Left Upper Lip Corner',
    'j_f_uslip_r': 'Right Upper Lip Corner',
    'j_f_dmlip_01_l': 'Left Lower Outer Lip (Lipline)',
    'j_f_dmlip_01_r': 'Right Lower Outer Lip (Lipline)',
    'j_f_dmlip_02_l': 'Left Lower Outer Lip (Opening)',
    'j_f_dmlip_02_r': 'Right Lower Outer Lip (Opening)',
    'j_f_dlip_01_l': 'Left Lower Center Lip (Lipline)',
    'j_f_dlip_01_r': 'Right Lower Center Lip (Lipline)',
    'j_f_dlip_02_l': 'Left Lower Center Lip (Opening)',
    'j_f_dlip_02_r': 'Right Lower Center Lip (Opening)',
    'j_f_dslip_l': 'Left Lower Lip Corner',
    'j_f_dslip_r': 'Right Lower Lip Corner',
    'j_f_bero_01': 'Tongue 01',
    'j_f_bero_02': 'Tongue 02',
    'j_f_bero_03': 'Tongue 03',
    'j_f_ago': 'Jaw (DT)',
    'j_f_dago': 'Lower Jaw/Chin (DT)',
    'j_f_hagukiup': 'Upper Teeth',
    'j_f_hagukidn': 'Lower Teeth',
    'j_f_hige_l': 'Left Whisker (Hrothgar)',
    'j_f_hige_r': 'Right Whisker (Hrothgar)',
    
    # Eye Area
    'j_f_mabup_01_l': 'Left Upper Center Eyelid',
    'j_f_mabup_01_r': 'Right Upper Center Eyelid',
    'j_f_mabup_02out_l': 'Left Upper Outer Corner Eyelid',
    'j_f_mabup_02out_r': 'Right Upper Outer Corner Eyelid',
    'j_f_mabup_03in_l': 'Left Upper Inner Corner Eyelid',
    'j_f_mabup_03in_r': 'Right Upper Inner Corner Eyelid',
    'j_f_mabdn_01_l': 'Left Lower Center Eyelid',
    'j_f_mabdn_01_r': 'Right Lower Center Eyelid',
    'j_f_mabdn_02out_l': 'Left Lower Outer Corner Eyelid',
    'j_f_mabdn_02out_r': 'Right Lower Outer Corner Eyelid',
    'j_f_mabdn_03in_l': 'Left Lower Inner Corner Eyelid',
    'j_f_mabdn_03in_r': 'Right Lower Inner Corner Eyelid',
    'j_f_mayu_l': 'Left Outer Eyebrow',
    'j_f_mayu_r': 'Right Outer Eyebrow',
    'j_f_mmayu_l': 'Left Inner Eyebrow',
    'j_f_mmayu_r': 'Right Inner Eyebrow',
    'j_f_miken_01_l': 'Left Brow Ridge',
    'j_f_miken_01_r': 'Right Brow Ridge',
    'j_f_miken_02_l': 'Left Inner Brow Ridge',
    'j_f_miken_02_r': 'Right Inner Brow Ridge',
    'j_f_eye_l': 'Left Eyeball',
    'j_f_eye_r': 'Right Eyeball',
    'j_f_mab_l': 'Left Eye Socket',
    'j_f_mab_r': 'Right Eye Socket',
    'j_f_eyepuru_l': 'Left Eyeball 2',
    'j_f_eyepuru_r': 'Right Eyeball 2',
    'j_f_irisprm_l': 'Left Iris (Gpose)',
    'j_f_irisprm_r': 'Right Iris (Gpose)',
    'j_f_eyeprm_01_l': 'Left Iris 3 (Gpose)',
    'j_f_eyeprm_01_r': 'Right Iris 3 (Gpose)',
    
    # Nose
    'j_f_uhana': 'Nose Bridge',
    'j_f_hana_l': 'Left Nostril',
    'j_f_hana_r': 'Right Nostril',
    'j_f_dmiken_l': 'Left Glabella',
    'j_f_dmiken_r': 'Right Glabella',
    
    # Cheeks
    'j_f_hoho_l': 'Left Cheek (Main)',
    'j_f_hoho_r': 'Right Cheek (Main)',
    'j_f_dhoho_l': 'Left Outer Cheek',
    'j_f_dhoho_r': 'Right Outer Cheek',
    'j_f_shoho_l': 'Left Middle Cheek',
    'j_f_shoho_r': 'Right Middle Cheek',
    'j_f_dmemoto_l': 'Left Inner Cheek',
    'j_f_dmemoto_r': 'Right Inner Cheek',
    
    # Pre-DT Face bones (may not exist on DT heads)
    'j_f_dmab_l': 'Left Lower Eyelid',
    'j_f_dmab_r': 'Right Lower Eyelid',
    'j_f_hana': 'Nose',
    'j_f_lip_l': 'Left Lip',
    'j_f_lip_r': 'Right Lip',
    'j_f_uago': 'Upper Lip A',
    'j_f_ulip': 'Upper Lip B',
    'n_f_lip_l': 'Left Lip (N)',
    'n_f_lip_r': 'Right Lip (N)',
    'n_f_ulip_l': 'Left Upper Lip',
    'n_f_ulip_r': 'Right Upper Lip',
    'j_f_dlip': 'Lower Lip',
    'j_f_memoto': 'Bridge',
    'j_f_miken_l': 'Left Brow',
    'j_f_miken_r': 'Right Brow',
    'j_f_umab_l': 'Left Upper Eyelid',
    'j_f_umab_r': 'Right Upper Eyelid',
    'j_f_face': 'Face',
    
    # Main/Offhand
    'mh_n_hara': 'Main Hand',
    'oh_n_hara': 'Offhand',
    'mh_n_root': 'Main Hand Root',
    'oh_n_root': 'Offhand Root',
    
    # Gear EX bones
    'j_ex_met_va': 'Visor A',
    'j_ex_met_vb': 'Visor B',
    
    # Modded Bones (IVCS1/IVCS2/YAS)
    'iv_c_mune_l': 'Left Breast B (Modded)',
    'iv_c_mune_r': 'Right Breast B (Modded)',
    'iv_nitoukin_l': 'Left Bicep (Modded)',
    'iv_nitoukin_r': 'Right Bicep (Modded)',
    'iv_shiri_l': 'Left Buttcheek (Modded)',
    'iv_shiri_r': 'Right Buttcheek (Modded)',
    'iv_fukubu_phys': 'Upper Belly (Modded)',
    'ya_fukubu_phys': 'Lower Belly (Modded)',
    'iv_daitai_phys_l': 'Left Back Thigh (Modded)',
    'iv_daitai_phys_r': 'Right Back Thigh (Modded)',
    'ya_daitai_phys_l': 'Left Front Thigh (Modded)',
    'ya_daitai_phys_r': 'Right Front Thigh (Modded)',
}


def get_readable_bone_name(bone_name):
    """Get a human-readable name for a bone, with fallback to original name"""
    return BONE_NAME_MAPPING.get(bone_name, bone_name)


# ---------------------------------------------------------------------------
# LivePose transform math
#
# In-game (Caraxi/LivePose, SkeletonService.ApplySnapshot), each stack of a
# .livepose file is applied to the bone's MODEL-SPACE transform (i.e. the
# transform relative to the skeleton root), not the bone-local transform:
#
#   model.Position += stack.Position                      (model space)
#   model.Rotation  = model.Rotation * stack.Rotation     (post-multiplied)
#   model.Scale    += stack.Scale
#
# Bones are processed parents-first and (with the usual Propogate=3 flag)
# children follow their parent's model-space change.
#
# A GLTF exported by XAT/VFXEdit stores raw game (havok) local transforms in
# its nodes, so the glTF scene space is identical to the game's model space.
# Blender's glTF importer converts every node TRS into Blender coordinates
# (glTF Y-up -> Blender Z-up, V = +90deg about X) and gives every bone a
# "bone direction" correction C(b) (rotation only):
#
#   pose_matrix(b) = V @ NodeGlobal(b) @ V^-1 @ C(b)
#
# For the default 'BLENDER' bone heuristic C(b) == V for every bone.
# If the source .gltf/.glb path is known, C(b) is computed exactly from the
# file's bind pose, which makes the math correct for any import heuristic.
# ---------------------------------------------------------------------------

# glTF -> Blender axis conversion (+90 deg about X)
LIVEPOSE_V_QUAT = mathutils.Quaternion((math.sqrt(0.5), math.sqrt(0.5), 0.0, 0.0))


def _get_v_mats():
    v = LIVEPOSE_V_QUAT.to_matrix().to_4x4()
    return v, v.inverted()


def _node_trs_to_matrix(node):
    """Convert a glTF node's local TRS/matrix to a mathutils Matrix."""
    if 'matrix' in node:
        # glTF matrices are column-major
        return mathutils.Matrix(
            (node['matrix'][0:4], node['matrix'][4:8], node['matrix'][8:12], node['matrix'][12:16])
        ).transposed()
    t = node.get('translation', [0.0, 0.0, 0.0])
    r = node.get('rotation', [0.0, 0.0, 0.0, 1.0])  # x, y, z, w
    s = node.get('scale', [1.0, 1.0, 1.0])
    quat = mathutils.Quaternion((r[3], r[0], r[1], r[2]))
    return mathutils.Matrix.LocRotScale(mathutils.Vector(t), quat, mathutils.Vector(s))


def _read_glb_json(filepath):
    """Extract the JSON chunk of a .glb file."""
    with open(filepath, 'rb') as f:
        magic, version, _length = struct.unpack('<4sII', f.read(12))
        if magic != b'glTF':
            raise ValueError('Not a GLB file')
        chunk_len, chunk_type = struct.unpack('<I4s', f.read(8))
        if chunk_type != b'JSON':
            raise ValueError('First GLB chunk is not JSON')
        return json.loads(f.read(chunk_len).decode('utf-8'))


def _parse_gltf_bind_globals(filepath):
    """Parse a .gltf/.glb file and return {node_name: bind global Matrix} in
    glTF (game) coordinates, or None on failure."""
    try:
        if filepath.lower().endswith('.glb'):
            data = _read_glb_json(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)

        nodes = data.get('nodes', [])
        parent = {}
        for i, node in enumerate(nodes):
            for child in node.get('children', []):
                parent[child] = i

        locals_mat = [_node_trs_to_matrix(n) for n in nodes]

        globals_mat = {}

        def compute_global(i):
            if i in globals_mat:
                return globals_mat[i]
            p = parent.get(i)
            if p is None:
                globals_mat[i] = locals_mat[i]
            else:
                globals_mat[i] = compute_global(p) @ locals_mat[i]
            return globals_mat[i]

        result = {}
        for i, node in enumerate(nodes):
            name = node.get('name')
            if name:
                result[name] = compute_global(i)
        return result
    except Exception as e:
        print(f"LivePose: could not parse source glTF for bone corrections: {e}")
        return None


def compute_bone_corrections(armature, source_gltf_path=None):
    """Compute the per-bone correction C(b) such that
        pose_matrix(b) = V @ NodeGlobal(b) @ V^-1 @ C(b)
    Returns {bone_name: 4x4 rotation Matrix}.
    Falls back to C = V (default 'BLENDER' import heuristic) for every bone.
    """
    v_mat, v_inv = _get_v_mats()
    corrections = {}

    bind_globals = None
    if source_gltf_path and os.path.exists(source_gltf_path):
        bind_globals = _parse_gltf_bind_globals(source_gltf_path)

    for bone in armature.data.bones:
        c = None
        if bind_globals is not None and bone.name in bind_globals:
            try:
                # matrix_local = V @ BindGlobal @ V^-1 @ C  =>  C = (V BG V^-1)^-1 @ matrix_local
                conv_bg = v_mat @ bind_globals[bone.name] @ v_inv
                c_full = conv_bg.inverted() @ bone.matrix_local
                # correction is a pure rotation; drop numerical residue
                _t, r, _s = c_full.decompose()
                c = r.to_matrix().to_4x4()
            except Exception:
                c = None
        if c is None:
            c = v_mat.copy()
        corrections[bone.name] = c
    return corrections


def bone_topo_order(armature):
    """All bone names, parents before children."""
    order = []

    def visit(bone):
        order.append(bone.name)
        for child in bone.children:
            visit(child)

    for bone in armature.data.bones:
        if bone.parent is None:
            visit(bone)
    return order


def collect_livepose_deltas(livepose_data, armature, enabled_bones=None):
    """Extract per-bone stack deltas from parsed LivePose JSON.

    Returns {bone_name: [(d_pos, d_quat, d_scale), ...]} in game coordinates,
    with stacks kept in file order. Bones missing from the armature are
    returned in 'skipped'.
    """
    bone_deltas = {}
    skipped = []
    for bone_data in livepose_data['Data']:
        if 'BonePoseInfoId' not in bone_data or 'Stacks' not in bone_data:
            continue

        bone_name = bone_data['BonePoseInfoId']['BoneName']

        if enabled_bones is not None and len(enabled_bones) > 0 and bone_name not in enabled_bones:
            continue

        if bone_name not in armature.pose.bones:
            skipped.append(bone_name)
            continue

        stacks = []
        for stack in bone_data['Stacks']:
            if 'Transform' not in stack:
                continue
            transform = stack['Transform']
            pos = transform.get('Position', {})
            rot = transform.get('Rotation', {})
            scl = transform.get('Scale', {})
            d_pos = mathutils.Vector((pos.get('X', 0.0), pos.get('Y', 0.0), pos.get('Z', 0.0)))
            # LivePose stores quaternions as XYZW, Blender uses WXYZ
            d_quat = mathutils.Quaternion((
                rot.get('W', 1.0), rot.get('X', 0.0), rot.get('Y', 0.0), rot.get('Z', 0.0)
            ))
            d_quat.normalize()
            d_scale = mathutils.Vector((scl.get('X', 0.0), scl.get('Y', 0.0), scl.get('Z', 0.0)))
            stacks.append((d_pos, d_quat, d_scale))

        if stacks:
            bone_deltas[bone_name] = stacks

    return bone_deltas, skipped


def filter_deltas_for_mode(stacks, apply_mode, invert=False):
    """Filter stack deltas by apply mode and optionally invert them.

    Inversion applies the stacks in reverse order with negated components
    (the exact inverse of the forward composition).
    """
    want_pos = apply_mode in ('ALL', 'POSITION', 'ROT_POS')
    want_rot = apply_mode in ('ALL', 'ROTATION', 'ROT_POS')
    want_scl = apply_mode in ('ALL', 'SCALE')

    result = []
    for d_pos, d_quat, d_scale in stacks:
        result.append((
            d_pos.copy() if want_pos else mathutils.Vector((0.0, 0.0, 0.0)),
            d_quat.copy() if want_rot else mathutils.Quaternion((1.0, 0.0, 0.0, 0.0)),
            d_scale.copy() if want_scl else mathutils.Vector((0.0, 0.0, 0.0)),
        ))

    if invert:
        inverted = []
        for d_pos, d_quat, d_scale in reversed(result):
            inverted.append((-d_pos, d_quat.conjugated(), -d_scale))
        result = inverted
    return result


class LivePoseBakeState:
    """Per-frame model-space application of LivePose deltas on an armature.

    Usage: create once per apply operation, then call process_frame() after
    each scene.frame_set(). Adjusted channels for delta bones are written to
    the pose bones (caller keyframes them if desired).

    Forward application: a delta bone's base pose is computed from its
    already-adjusted parent (children follow their parent - "Propogate").

    Invert (removal): the animation currently contains the forward-baked
    result. A baked local was created relative to the parent's FORWARD pose,
    so a delta bone's base must be its evaluated (still-adjusted) pose,
    not a pose recomputed from its already-reverted parent.
    """

    def __init__(self, armature, bone_deltas, apply_mode, invert=False, source_gltf_path=None):
        self.armature = armature
        self.apply_mode = apply_mode
        self.invert = invert
        self.v_mat, self.v_inv = _get_v_mats()
        self.corrections = compute_bone_corrections(armature, source_gltf_path)
        self.order = bone_topo_order(armature)

        # rest data
        self.rest_local = {}      # bone -> armature-space rest matrix
        self.rel_rest = {}        # bone -> rest matrix relative to parent
        self.no_inherit_scale = set()
        for bone in armature.data.bones:
            self.rest_local[bone.name] = bone.matrix_local.copy()
            if bone.parent is not None:
                self.rel_rest[bone.name] = bone.parent.matrix_local.inverted() @ bone.matrix_local
                if bone.inherit_scale == 'NONE':
                    self.no_inherit_scale.add(bone.name)
            else:
                self.rel_rest[bone.name] = bone.matrix_local.copy()

        # filtered deltas per bone
        self.deltas = {
            name: filter_deltas_for_mode(stacks, apply_mode, invert)
            for name, stacks in bone_deltas.items()
        }

        self.pose_mats = {}       # bone -> post-delta armature-space matrix (current frame)
        self.prev_quat = {}       # bone -> last written quaternion (sign continuity)

        self.want_pos = apply_mode in ('ALL', 'POSITION', 'ROT_POS')
        self.want_rot = apply_mode in ('ALL', 'ROTATION', 'ROT_POS')
        self.want_scl = apply_mode in ('ALL', 'SCALE')

    def _parent_mat(self, bone_name, parent_pose):
        """Parent pose matrix for composing a child, honoring the child's
        inherit_scale setting ('NONE' strips the parent's scale)."""
        if bone_name in self.no_inherit_scale:
            t, r, _s = parent_pose.decompose()
            return mathutils.Matrix.LocRotScale(t, r, mathutils.Vector((1.0, 1.0, 1.0)))
        return parent_pose

    def process_frame(self):
        """Compute adjusted pose for the current frame. Must be called after
        scene.frame_set(); bones are processed parents-first."""
        self.pose_mats = {}

        # Read all channel values and compute the evaluated pose of every
        # bone BEFORE writing anything (FK evaluation of the current action).
        bases = {}
        eval_pose = {}
        for bone_name in self.order:
            posebone = self.armature.pose.bones[bone_name]
            bone = self.armature.data.bones[bone_name]
            basis = posebone.matrix_basis.copy()
            bases[bone_name] = basis
            if bone.parent is not None and bone.parent.name in eval_pose:
                eval_pose[bone_name] = self._parent_mat(bone_name, eval_pose[bone.parent.name]) @ self.rel_rest[bone_name] @ basis
            else:
                eval_pose[bone_name] = self.rest_local[bone_name] @ basis

        for bone_name in self.order:
            posebone = self.armature.pose.bones[bone_name]
            bone = self.armature.data.bones[bone_name]
            stacks = self.deltas.get(bone_name)
            parent_name = bone.parent.name if bone.parent is not None else None

            if self.invert:
                # Removal: the animation currently holds the forward-baked
                # result. A delta bone's base is its evaluated (still fully
                # adjusted) pose; after removing its own stacks the bone holds
                # its original local relative to the EVALUATED (pre-removal)
                # parent, so the basis is written relative to that parent.
                if not stacks:
                    continue
                base = eval_pose[bone_name]
                new_pose = self._apply_stacks(bone_name, base, stacks)
                if parent_name is not None and parent_name in eval_pose:
                    parent_mat = self._parent_mat(bone_name, eval_pose[parent_name])
                    basis_new = self.rel_rest[bone_name].inverted() @ parent_mat.inverted() @ new_pose
                else:
                    basis_new = self.rest_local[bone_name].inverted() @ new_pose
                self._write_basis_values(posebone, basis_new)
                self.pose_mats[bone_name] = new_pose
                continue

            # Forward application: children follow their already-adjusted
            # parent (LivePose "Propogate" behaviour).
            if parent_name is not None and parent_name in self.pose_mats:
                base = self._parent_mat(bone_name, self.pose_mats[parent_name]) @ self.rel_rest[bone_name] @ bases[bone_name]
            else:
                base = self.rest_local[bone_name] @ bases[bone_name]

            if stacks:
                base = self._apply_stacks(bone_name, base, stacks)
                if parent_name is not None and parent_name in self.pose_mats:
                    parent_mat = self._parent_mat(bone_name, self.pose_mats[parent_name])
                    basis_new = self.rel_rest[bone_name].inverted() @ parent_mat.inverted() @ base
                else:
                    basis_new = self.rest_local[bone_name].inverted() @ base
                self._write_basis_values(posebone, basis_new)

            self.pose_mats[bone_name] = base

    def _apply_stacks(self, bone_name, base_pose, stacks):
        """Apply the bone's stacks in game model space."""
        c = self.corrections[bone_name]
        # game model-space transform
        node_global = self.v_inv @ base_pose @ c.inverted() @ self.v_mat
        t, r, s = node_global.decompose()

        for d_pos, d_quat, d_scale in stacks:
            t = t + d_pos
            r = r @ d_quat
            r.normalize()
            s = s + d_scale

        node_global = mathutils.Matrix.LocRotScale(t, r, s)
        return self.v_mat @ node_global @ self.v_inv @ c

    def _write_basis_values(self, posebone, basis_new):
        """Store an adjusted pose-bone basis on the pose bone (no keyframing
        here)."""
        loc, rot, scale = basis_new.decompose()

        # quaternion sign continuity (avoid interpolation flips)
        prev = self.prev_quat.get(posebone.name)
        if prev is not None and rot.dot(prev) < 0:
            rot.negate()
        self.prev_quat[posebone.name] = rot.copy()

        if self.want_pos:
            posebone.location = loc
        if self.want_rot:
            posebone.rotation_mode = 'QUATERNION'
            posebone.rotation_quaternion = rot
        if self.want_scl:
            posebone.scale = scale


# CustomizePlus helper functions (adapted from sleepbnuuy's bustomize plugin)
def translate_cplus_hash(cplus_hash: str):
    """Decode and parse CustomizePlus string"""
    try:
        bytes_data = base64.b64decode(cplus_hash)
        bytes_array = bytearray(bytes_data)
        decomp = zlib.decompress(bytes_array, zlib.MAX_WBITS | 16)
        version = decomp[0]
        json_str = decomp.decode('utf-8')
        cplus_dict = json.loads(json_str[1:])
        return version, cplus_dict
    except Exception as e:
        print(f"Failed to parse CustomizePlus string: {str(e)}")
        return None, None


def get_cplus_bone_scales(cplus_dict: dict):
    """Extract bone scaling data from CustomizePlus dictionary"""
    bones = cplus_dict.get('Bones', {})
    scale_dict = {}
    for bone_name, bone_data in bones.items():
        scaling = bone_data.get('Scaling', {})
        if scaling:
            scale_dict[bone_name] = scaling
    return scale_dict


def apply_cplus_scaling(armature, scale_dict):
    """Apply CustomizePlus scaling to armature pose bones"""
    applied_count = 0
    for posebone in armature.pose.bones:
        posebone.bone.inherit_scale = 'NONE'
        if posebone.name in scale_dict:
            scale_vector = scale_dict[posebone.name]
            posebone.scale = mathutils.Vector((
                scale_vector.get('X', 1.0),
                scale_vector.get('Y', 1.0),
                scale_vector.get('Z', 1.0)
            ))
            applied_count += 1
    return applied_count


def reset_cplus_scaling(armature):
    """Reset CustomizePlus scaling on armature"""
    for posebone in armature.pose.bones:
        posebone.bone.inherit_scale = 'FULL'
        posebone.scale = mathutils.Vector((1.0, 1.0, 1.0))


def normalize_action_whole_frames(action):
    """Resample all fcurves of the action so keys sit exactly on whole frames.

    Imported glTF animations usually have keys at fractional frames (e.g.
    238.9998 instead of 239) due to float precision. The glTF exporter
    samples animations at whole frames, so keys must be whole-frame aligned
    for baked content to survive the export.

    Returns (start_frame, end_frame, normalized_curve_count) or None if the
    action has no keyframes.
    """
    min_frame = float('inf')
    max_frame = float('-inf')

    for fcurve in action.fcurves:
        for keyframe in fcurve.keyframe_points:
            min_frame = min(min_frame, keyframe.co[0])
            max_frame = max(max_frame, keyframe.co[0])

    if min_frame == float('inf') or max_frame == float('-inf'):
        return None

    start_frame = int(round(min_frame))
    end_frame = int(round(max_frame))

    normalized_count = 0
    for fcurve in action.fcurves:
        if len(fcurve.keyframe_points) == 0:
            continue

        frame_values = {}
        for frame in range(start_frame, end_frame + 1):
            frame_values[frame] = fcurve.evaluate(frame)

        while len(fcurve.keyframe_points) > 0:
            fcurve.keyframe_points.remove(fcurve.keyframe_points[0])

        for frame, value in sorted(frame_values.items()):
            keyframe = fcurve.keyframe_points.insert(frame, value)
            keyframe.interpolation = 'LINEAR'

        normalized_count += 1

    for fcurve in action.fcurves:
        fcurve.update()

    return start_frame, end_frame, normalized_count


def clear_animation_scale_keyframes(action):
    """Remove all scale keyframes from an action"""
    if not action:
        return 0
    
    removed_count = 0
    fcurves_to_remove = []
    
    for fcurve in action.fcurves:
        if fcurve.data_path.endswith('.scale'):
            fcurves_to_remove.append(fcurve)
    
    for fcurve in fcurves_to_remove:
        action.fcurves.remove(fcurve)
        removed_count += 1
    
    return removed_count


def update_livepose_filepath(self, context):
    """Callback when livepose filepath is changed - parse bones from file"""
    settings = context.scene.livepose_settings
    
    # Clear existing bone list
    settings.bone_toggles.clear()
    
    # If no file selected, return early
    if not settings.livepose_filepath or not os.path.exists(settings.livepose_filepath):
        return
    
    # Try to load and parse the livepose file
    try:
        with open(settings.livepose_filepath, 'r') as f:
            livepose_data = json.load(f)
        
        if 'Data' in livepose_data:
            # Extract all unique bone names
            bone_names = set()
            for bone_data in livepose_data['Data']:
                if 'BonePoseInfoId' in bone_data and 'Stacks' in bone_data:
                    bone_name = bone_data['BonePoseInfoId']['BoneName']
                    if bone_name:
                        bone_names.add(bone_name)
            
            # Add bones to the toggle list (sorted alphabetically)
            for bone_name in sorted(bone_names):
                item = settings.bone_toggles.add()
                item.name = bone_name
                item.enabled = True  # Default to enabled
    except Exception as e:
        print(f"Failed to parse LivePose file: {str(e)}")


class BoneToggleItem(bpy.types.PropertyGroup):
    """Property group to store individual bone toggle state"""
    name: StringProperty(
        name="Bone Name",
        description="Name of the bone",
        default=""
    ) # type: ignore
    
    enabled: BoolProperty(
        name="Enabled",
        description="Whether to apply this bone's transformation",
        default=True
    ) # type: ignore


def update_target_armature(self, context):
    """Callback when target armature is changed"""
    if not self.target_armature:
        return
    
    # List of objects to update with the armature modifier
    target_objects = ["Mannequin", "Face", "Tail"]
    
    for obj_name in target_objects:
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            
            # Find or create armature modifier
            armature_mod = None
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE':
                    armature_mod = mod
                    break
            
            # Create armature modifier if it doesn't exist
            if not armature_mod:
                armature_mod = obj.modifiers.new(name="Armature", type='ARMATURE')
            
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
        subtype='FILE_PATH',
        update=update_livepose_filepath
    ) # type: ignore
    
    bone_toggles: CollectionProperty(
        type=BoneToggleItem,
        name="Bone Toggles",
        description="List of bones with toggle states"
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
    
    # CustomizePlus integration
    cplus_string: StringProperty(
        name="CustomizePlus String",
        description="Paste CustomizePlus string here to apply bone scaling",
        default=""
    ) # type: ignore
    
    apply_cplus_on_import: BoolProperty(
        name="Apply C+ Scaling on Import",
        description="Automatically clear animation scale keyframes and apply CustomizePlus scaling",
        default=False
    ) # type: ignore
    
    cplus_scaling_applied: bpy.props.BoolProperty(default=False) # type: ignore


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
        
        # Bone Toggle List
        if len(settings.bone_toggles) > 0:
            box = layout.box()
            box.label(text='Bones to Apply:', icon='BONE_DATA')
            
            # Add buttons to toggle all/none
            row = box.row(align=True)
            row.operator("livepose.toggle_all_bones", text="All").enable = True
            row.operator("livepose.toggle_all_bones", text="None").enable = False
            
            # Create a scrollable list of bones with readable names
            col = box.column(align=True)
            for bone_item in settings.bone_toggles:
                row = col.row(align=True)
                row.prop(bone_item, "enabled", text="")
                # Display: "Readable Name (technical_name)"
                readable_name = get_readable_bone_name(bone_item.name)
                if readable_name != bone_item.name:
                    display_text = f"{readable_name} ({bone_item.name})"
                else:
                    display_text = bone_item.name
                row.label(text=display_text)

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
        row.operator("livepose.normalize_animation", text="Normalize Animation", icon="NORMALIZE_FCURVES")
        
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
        
        # CustomizePlus Integration
        box.separator()
        box.label(text='CustomizePlus (C+):', icon='MOD_ARMATURE')
        box.prop(settings, "cplus_string", text="C+ String")
        box.prop(settings, "apply_cplus_on_import", text="Apply C+ on Import")
        
        if settings.cplus_scaling_applied:
            row = box.row()
            row.label(text="C+ Scaling Applied", icon="CHECKMARK")
        
        box.separator()
        box.prop(settings, "gltf_export_path", text="Export Folder")
        box.prop(settings, "gltf_export_filename", text="Filename")
        row = box.row()
        row.operator("livepose.export_gltf", text="Export GLTF", icon="EXPORT")


class LIVEPOSE_OT_ToggleAllBones(bpy.types.Operator):
    bl_idname = "livepose.toggle_all_bones"
    bl_label = "Toggle All Bones"
    bl_description = "Enable or disable all bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    enable: BoolProperty(default=True) # type: ignore
    
    def execute(self, context):
        settings = context.scene.livepose_settings
        for bone_item in settings.bone_toggles:
            bone_item.enabled = self.enable
        return {'FINISHED'}


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

        # Build a set of enabled bones for quick lookup
        enabled_bones = {item.name for item in settings.bone_toggles if item.enabled}

        bone_deltas, skipped_bones = collect_livepose_deltas(livepose_data, target_armature, enabled_bones)

        if not bone_deltas:
            self.report({'WARNING'}, "No matching bones found in LivePose data")
            return {'CANCELLED'}

        source_gltf = target_armature.get("livepose_source_gltf", None)
        state = LivePoseBakeState(target_armature, bone_deltas, settings.apply_mode,
                                  settings.invert_transform, source_gltf)

        # Process the current frame (bones are handled parents-first internally)
        context.view_layer.update()
        state.process_frame()

        applied_count = len(bone_deltas)

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

        # Build a set of enabled bones for quick lookup
        enabled_bones = {item.name for item in settings.bone_toggles if item.enabled}

        bone_deltas, skipped_bones = collect_livepose_deltas(livepose_data, target_armature, enabled_bones)

        if not bone_deltas:
            self.report({'WARNING'}, "No matching bones found in LivePose data")
            return {'CANCELLED'}

        # Normalize the action so all keys sit on whole frames. Imported
        # glTF animations usually have keys at fractional frames (e.g.
        # 238.9998 instead of 239); keyframe insertion merges into those
        # nearby keys and the glTF exporter only samples whole frames, so
        # normalization is required for the bake to cover the full animation.
        result = normalize_action_whole_frames(action)
        if result is None:
            self.report({'WARNING'}, "No keyframes found in action")
            return {'CANCELLED'}

        start_frame, end_frame, _ = result
        frame_numbers = list(range(start_frame, end_frame + 1))
        original_frame = context.scene.frame_current

        self.report({'INFO'}, f"Processing {len(frame_numbers)} frames from {frame_numbers[0]} to {frame_numbers[-1]}")

        source_gltf = target_armature.get("livepose_source_gltf", None)
        state = LivePoseBakeState(target_armature, bone_deltas, settings.apply_mode,
                                  settings.invert_transform, source_gltf)

        modified_bones = set(bone_deltas.keys())

        # Process each frame individually
        for frame in frame_numbers:
            # Set to the exact frame to ensure we're reading the correct keyframe values
            context.scene.frame_set(frame)
            # Force update to ensure pose is evaluated
            context.view_layer.update()

            state.process_frame()

            # Bake the adjusted channels for all delta bones
            for bone_name in bone_deltas:
                posebone = target_armature.pose.bones[bone_name]
                if state.want_pos:
                    posebone.keyframe_insert(data_path="location", frame=frame)
                if state.want_rot:
                    posebone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                if state.want_scl:
                    posebone.keyframe_insert(data_path="scale", frame=frame)

        # Restore original frame
        context.scene.frame_set(original_frame)
        context.view_layer.update()

        if skipped_bones:
            self.report({'WARNING'}, f"Skipped {len(skipped_bones)} missing bones: {', '.join(skipped_bones[:5])}{'...' if len(skipped_bones) > 5 else ''}")

        action_text = "Removed" if settings.invert_transform else "Applied"
        self.report({'INFO'}, f"{action_text} LivePose offset to {len(modified_bones)} bones across {len(frame_numbers)} keyframes")
        settings.pose_was_applied = True
        return {'FINISHED'}


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

            # Remember the source file so LivePose application can derive the
            # exact per-bone corrections from its bind pose
            armature["livepose_source_gltf"] = self.filepath
            
            # Set frame range based on imported animation
            if armature.animation_data and armature.animation_data.action:
                action = armature.animation_data.action
                frame_start = None
                frame_end = None
                
                # Find the min and max keyframe times across all fcurves
                for fcurve in action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        frame = keyframe.co[0]
                        if frame_start is None or frame < frame_start:
                            frame_start = frame
                        if frame_end is None or frame > frame_end:
                            frame_end = frame
                
                if frame_start is not None and frame_end is not None:
                    # Round (not truncate) so fractional keys like 238.9998
                    # don't lose the actual last frame (239)
                    context.scene.frame_start = int(round(frame_start))
                    context.scene.frame_end = int(round(frame_end))
                    self.report({'INFO'}, f"Set frame range: {int(round(frame_start))} to {int(round(frame_end))}")
            
            # Apply CustomizePlus scaling if enabled
            settings = context.scene.livepose_settings
            if settings.apply_cplus_on_import and settings.cplus_string:
                # Parse CustomizePlus string
                version, cplus_dict = translate_cplus_hash(settings.cplus_string)
                
                if version == 4 and cplus_dict:
                    # Clear scale keyframes from animation if it exists
                    if armature.animation_data and armature.animation_data.action:
                        removed = clear_animation_scale_keyframes(armature.animation_data.action)
                        if removed > 0:
                            self.report({'INFO'}, f"Cleared {removed} scale keyframes from animation")
                    
                    # Apply CustomizePlus scaling
                    scale_dict = get_cplus_bone_scales(cplus_dict)
                    applied = apply_cplus_scaling(armature, scale_dict)
                    settings.cplus_scaling_applied = True
                    self.report({'INFO'}, f"Applied CustomizePlus scaling to {applied} bones")
                elif version != 4:
                    self.report({'WARNING'}, f"CustomizePlus version {version} not supported (expected 4)")
                else:
                    self.report({'WARNING'}, "Failed to parse CustomizePlus string")
        
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
        
        # Reset CustomizePlus scaling before export if it was applied
        cplus_was_applied = settings.cplus_scaling_applied
        if cplus_was_applied:
            reset_cplus_scaling(target_armature)
            self.report({'INFO'}, "Reset CustomizePlus scaling for export")
        
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
                export_frame_range=False,  # Export full action range, not the scene playback range
                
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
            # Re-apply CustomizePlus scaling if it was reset
            if cplus_was_applied and settings.cplus_string:
                version, cplus_dict = translate_cplus_hash(settings.cplus_string)
                if version == 4 and cplus_dict:
                    scale_dict = get_cplus_bone_scales(cplus_dict)
                    apply_cplus_scaling(target_armature, scale_dict)
            return {'CANCELLED'}
        
        # Re-apply CustomizePlus scaling after successful export
        if cplus_was_applied and settings.cplus_string:
            version, cplus_dict = translate_cplus_hash(settings.cplus_string)
            if version == 4 and cplus_dict:
                scale_dict = get_cplus_bone_scales(cplus_dict)
                apply_cplus_scaling(target_armature, scale_dict)
                self.report({'INFO'}, "Re-applied CustomizePlus scaling after export")
        
        self.report({'INFO'}, f"Successfully exported GLTF: {filename}")
        return {'FINISHED'}


class LIVEPOSE_OT_NormalizeAnimation(bpy.types.Operator):
    bl_idname = "livepose.normalize_animation"
    bl_label = "Normalize Animation"
    bl_description = "Normalize animation by placing keyframes exactly on each frame. Fixes issues with FFXIV not handling offset keyframes well"
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
            self.report({'ERROR'}, "No active action to normalize")
            return {'CANCELLED'}
        
        action = target_armature.animation_data.action

        # Get the frame range of the animation
        if len(action.fcurves) == 0:
            self.report({'WARNING'}, "Action has no fcurves to normalize")
            return {'CANCELLED'}

        result = normalize_action_whole_frames(action)
        if result is None:
            self.report({'WARNING'}, "Could not determine frame range")
            return {'CANCELLED'}

        start_frame, end_frame, normalized_count = result
        self.report({'INFO'}, f"Normalized {normalized_count} animation curves from frame {start_frame} to {end_frame}")
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
    BoneToggleItem,
    LivePoseSettings,
    LIVEPOSE_PT_MainPanel,
    LIVEPOSE_OT_ToggleAllBones,
    LIVEPOSE_OT_ApplyPose,
    LIVEPOSE_OT_ResetPose,
    LIVEPOSE_OT_ImportGLTF,
    LIVEPOSE_OT_ExportGLTF,
    LIVEPOSE_OT_NormalizeAnimation,
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
