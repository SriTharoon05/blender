import bpy, json
print(json.dumps({'version':bpy.app.version_string,'file':bpy.data.filepath,'objects':[(o.name,o.type) for o in bpy.data.objects], 'engine':bpy.context.scene.render.engine},indent=2))
