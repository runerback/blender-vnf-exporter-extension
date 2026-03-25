# blender-vnf-exporter-extension

Export blender mesh to [OpenSCAD](https://openscad.org/) [VNF](https://github.com/BelfrySCAD/BOSL2/wiki/Tutorial-VNF) *(module with [BOSL2](https://github.com/BelfrySCAD/BOSL2))*

![featured](./assets/featured.png)

## Export flow

From Edit Mesh mode, use `Mesh > Export VNF`.

The add-on now shows a confirm dialog before the save-file dialog. In that confirm step you can set:
- file basename (also used as default `.scad` filename and module name)
- `Use Module`
- rotate `X/Y/Z` (degrees)
- scale `X/Y/Z`
- `Uniform Scale` (editing any one scale axis keeps all three axes synchronized)
- defaults: rotate `0.0`, scale `1.0` (GUI reset restores these values)

Default naming behavior:
- basename starts from the mesh object name
- the value is sanitized to be filename-safe (invalid characters replaced)
- if sanitization becomes empty, fallback name is `export`

Transform behavior:
- transforms are applied only to cloned export geometry (the original mesh is not modified)
- transform order is scale first, then rotate in X -> Y -> Z order

SCAD output behavior:
- `Use Module = true`: keep module-only output behavior
- `Use Module = false`: append `{module_name}();` as the last line
