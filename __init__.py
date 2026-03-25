bl_info = {
    "name": "Export VNF",
    "blender": (2, 80, 0),
    "category": "Mesh",
}

import bpy
import math
import os
import re
import bmesh
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator, VIEW3D_MT_edit_mesh
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.utils import register_class, unregister_class
from mathutils import Matrix


def _default_basename(context):
    mesh = context.edit_object or context.object
    if mesh and mesh.name:
        return _sanitize_name(mesh.name)
    # end if
    return "export"


# end def


def _sanitize_name(name):
    sanitized = name.strip()
    sanitized = re.sub(r"[^\w-]+", "_", sanitized)
    sanitized = sanitized.strip(" ._-")
    if not sanitized:
        return "export"
    # end if
    if sanitized[0].isdigit():
        sanitized = "_{}".format(sanitized)
    # end if
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if sanitized.upper() in reserved_names:
        sanitized = "{}_".format(sanitized)
    # end if
    return sanitized


# end def


def _apply_uniform_scale_from_last_axis(operator):
    axis = operator.scale_last_axis
    value = operator.scale_x
    if axis == "Y":
        value = operator.scale_y
    elif axis == "Z":
        value = operator.scale_z
    # end if

    operator.syncing_scale = True
    operator.scale_x = value
    operator.scale_y = value
    operator.scale_z = value
    operator.syncing_scale = False


# end def


def _update_scale_axis(axis):
    def _update(self, context):
        if self.syncing_scale:
            return
        # end if
        self.scale_last_axis = axis
        if self.uniform_scale:
            _apply_uniform_scale_from_last_axis(self)
        # end if

    # end def

    return _update


# end def


def _update_uniform_scale(self, context):
    if self.syncing_scale:
        return
    # end if
    if self.uniform_scale:
        _apply_uniform_scale_from_last_axis(self)
    # end if


# end def


class MeshVNFExportConfirm(Operator):
    """Collect export options before opening file save dialog"""

    bl_idname = "mesh.export_vnf_confirm"
    bl_label = "Export VNF Options"

    basename: StringProperty(
        name="File Basename",
        default="",
    )

    use_module: BoolProperty(
        name="Use Module",
        description="Enabled keeps module-only output; disabled appends module call line",
        default=True,
    )

    rotate_x: FloatProperty(
        name="Rotate X",
        description="Rotate around X axis (degrees)",
        default=0.0,
    )
    rotate_y: FloatProperty(
        name="Rotate Y",
        description="Rotate around Y axis (degrees)",
        default=0.0,
    )
    rotate_z: FloatProperty(
        name="Rotate Z",
        description="Rotate around Z axis (degrees)",
        default=0.0,
    )

    scale_x: FloatProperty(
        name="Scale X",
        description="Scale factor on X axis",
        default=1.0,
        update=_update_scale_axis("X"),
    )
    scale_y: FloatProperty(
        name="Scale Y",
        description="Scale factor on Y axis",
        default=1.0,
        update=_update_scale_axis("Y"),
    )
    scale_z: FloatProperty(
        name="Scale Z",
        description="Scale factor on Z axis",
        default=1.0,
        update=_update_scale_axis("Z"),
    )
    uniform_scale: BoolProperty(
        name="Uniform Scale",
        description="Use last changed scale axis for all axes",
        default=False,
        update=_update_uniform_scale,
    )

    scale_last_axis: StringProperty(default="X", options={"HIDDEN"})
    syncing_scale: BoolProperty(default=False, options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        if not self.basename:
            self.basename = _default_basename(context)
        # end if
        return context.window_manager.invoke_props_dialog(self)

    # end def

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "basename")
        layout.prop(self, "use_module")
        layout.separator()
        layout.label(text="Rotate (degrees)")
        layout.prop(self, "rotate_x")
        layout.prop(self, "rotate_y")
        layout.prop(self, "rotate_z")
        layout.separator()
        layout.label(text="Scale")
        layout.prop(self, "scale_x")
        layout.prop(self, "scale_y")
        layout.prop(self, "scale_z")
        layout.prop(self, "uniform_scale")

    # end def

    def execute(self, context):
        basename = self.basename.strip() or _default_basename(context)
        basename = _sanitize_name(basename)

        blend_dir = bpy.path.abspath("//")
        if not blend_dir:
            blend_dir = os.getcwd()
        # end if
        filepath = os.path.join(blend_dir, "{}.scad".format(basename))

        bpy.ops.mesh.export_vnf(
            "INVOKE_DEFAULT",
            filepath=filepath,
            module_name=basename,
            use_module=self.use_module,
            rotate_x=self.rotate_x,
            rotate_y=self.rotate_y,
            rotate_z=self.rotate_z,
            scale_x=self.scale_x,
            scale_y=self.scale_y,
            scale_z=self.scale_z,
            uniform_scale=self.uniform_scale,
            scale_last_axis=self.scale_last_axis,
        )
        return {"FINISHED"}

    # end def


# end class


class MeshVNFExporter(Operator, ExportHelper):
    """VNF Export Script"""

    bl_idname = "mesh.export_vnf"
    bl_label = "Export VNF"
    bl_options = {"PRESET"}

    module_name: StringProperty(default="", options={"HIDDEN"})

    filename_ext = ".scad"
    filter_glob: StringProperty(default="*.scad", options={"HIDDEN"})

    use_module: BoolProperty(
        name="Use Module",
        description="Enabled keeps module-only output; disabled appends module call line",
        default=True,
        options={"HIDDEN"},
    )
    rotate_x: FloatProperty(default=0.0, options={"HIDDEN"})
    rotate_y: FloatProperty(default=0.0, options={"HIDDEN"})
    rotate_z: FloatProperty(default=0.0, options={"HIDDEN"})
    scale_x: FloatProperty(default=1.0, options={"HIDDEN"})
    scale_y: FloatProperty(default=1.0, options={"HIDDEN"})
    scale_z: FloatProperty(default=1.0, options={"HIDDEN"})
    uniform_scale: BoolProperty(default=False, options={"HIDDEN"})
    scale_last_axis: StringProperty(default="X", options={"HIDDEN"})

    def draw(self, context):
        pass

    # end def

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            self.report({"WARNING"}, "enter edit mode")
            return {"CANCELLED"}
        # end if
        mesh = context.edit_object
        if not mesh or not mesh.data:
            self.report({"WARNING"}, "select one mesh")
            return {"CANCELLED"}
        # end if

        origin_bm = bmesh.from_edit_mesh(mesh.data)
        origin_tris_idx = {
            face.index: face for face in origin_bm.faces if len(face.verts) == 3
        }

        exporting_bm = origin_bm.copy()
        exporting_bm.verts.ensure_lookup_table()
        exporting_bm.edges.ensure_lookup_table()
        exporting_bm.faces.ensure_lookup_table()

        scale_x = self.scale_x
        scale_y = self.scale_y
        scale_z = self.scale_z
        if self.uniform_scale:
            uniform_scale = scale_x
            if self.scale_last_axis == "Y":
                uniform_scale = scale_y
            elif self.scale_last_axis == "Z":
                uniform_scale = scale_z
            # end if
            scale_x = uniform_scale
            scale_y = uniform_scale
            scale_z = uniform_scale
        # end if

        scale_matrix = Matrix.Diagonal((scale_x, scale_y, scale_z, 1.0))
        bmesh.ops.transform(
            exporting_bm,
            matrix=scale_matrix,
            verts=exporting_bm.verts,
        )
        for axis, degree in (
            ("X", self.rotate_x),
            ("Y", self.rotate_y),
            ("Z", self.rotate_z),
        ):
            if degree == 0.0:
                continue
            # end if
            rotate_matrix = Matrix.Rotation(math.radians(degree), 4, axis)
            bmesh.ops.transform(
                exporting_bm,
                matrix=rotate_matrix,
                verts=exporting_bm.verts,
            )
        # end for

        tri_meshs = bmesh.ops.triangulate(
            exporting_bm,
            faces=exporting_bm.faces,
            quad_method="BEAUTY",
            ngon_method="BEAUTY",
        )
        face_idx_map = {}
        for k, v in tri_meshs["face_map"].items():
            face_idx_map[v] = face_idx_map.get(v, []) + [k]
        # end for

        face_map = {
            key.index: value for key, value in face_idx_map.items()
        } | origin_tris_idx
        faces = {}
        for fdx, f in face_map.items():
            if isinstance(f, list):
                for fi in f:
                    faces[fi.index] = fi.verts
                # end for
            else:
                faces[fdx] = f.verts
            # end if
        # end for
        faceIdxes = list(faces.keys())
        faceIdxes.sort()
        vdxess = [[v.index for v in faces.get(idx)] for idx in faceIdxes]

        module_name = self.module_name.strip()
        if not module_name:
            module_name, _ = os.path.splitext(os.path.basename(self.filepath))
        # end if
        if not module_name:
            module_name = _default_basename(context)
        # end if
        module_name = _sanitize_name(module_name)
        self.module_name = module_name

        with open(self.filepath, "w", encoding="utf-8") as scad:
            lines = [
                "include <BOSL2/std.scad>",
                "module {}() {{".format(self.module_name),
                "    verts = [",
            ]
            for v in exporting_bm.verts:
                x, y, z = tuple(v.co)
                lines.append(f"        [{x},{y},{z}],")
            # end for
            lines.extend(["    ];", "    faces = ["])
            for vdxes in vdxess:
                lines.append(f"        {vdxes},")
            # end for
            lines.extend(["    ];", "    polyhedron(verts, faces);", "}"])
            if not self.use_module:
                lines.append("{}();".format(self.module_name))
            # end if
            scad.write("\n".join(lines))
        # end with

        exporting_bm.free()

        self.report({"INFO"}, "exported to: {}".format(self.filepath))
        return {"FINISHED"}

    # end def


# end class


def menu_func(self, context):
    self.layout.operator(MeshVNFExportConfirm.bl_idname)


# end def


def register():
    register_class(MeshVNFExportConfirm)
    register_class(MeshVNFExporter)
    VIEW3D_MT_edit_mesh.append(menu_func)


# end def


def unregister():
    VIEW3D_MT_edit_mesh.remove(menu_func)
    unregister_class(MeshVNFExporter)
    unregister_class(MeshVNFExportConfirm)


# end def


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
# end if
