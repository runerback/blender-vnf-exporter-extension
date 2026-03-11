bl_info = {
    "name": "Export VNF",
    "blender": (2, 80, 0),
    "category": "Mesh",
}

import os
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator, VIEW3D_MT_edit_mesh
from bpy.props import StringProperty, BoolProperty
from bpy.utils import register_class, unregister_class
import bmesh


class MeshVNFExporter(Operator, ExportHelper):
    """VNF Export Script"""

    bl_idname = "mesh.export_vnf"
    bl_label = "Export VNF"
    bl_options = {"PRESET"}

    module_name: StringProperty(default="", options={"HIDDEN"})

    def __init__(self):
        self.module_name, _ = os.path.splitext(os.path.basename(self.filepath))

    # end def

    filename_ext = ".scad"
    filter_glob: StringProperty(default="*.scad", options={"HIDDEN"})

    modulize: BoolProperty(
        name="Modulize",
        description="whether create module",
        default=False,
        options={"HIDDEN"},
    )

    def draw(self):
        layout = self.layout

        # TODO
        # row = layout.row()
        # row.prop(self, "module_name")

        row = layout.row()
        row.prop(self, "modulize")

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
            if self.modulize:
                lines.append("{}();".format(self.module_name))
            # end if
            scad.write("\n".join(lines))
        # end with

        self.report({"INFO"}, "exported to: {}".format(self.filepath))
        return {"FINISHED"}

    # end def


# end class


def menu_func(self, context):
    self.layout.operator(MeshVNFExporter.bl_idname)


# end def


def register():
    register_class(MeshVNFExporter)
    VIEW3D_MT_edit_mesh.append(menu_func)


# end def


def unregister():
    VIEW3D_MT_edit_mesh.remove(menu_func)
    unregister_class(MeshVNFExporter)


# end def


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
# end if
