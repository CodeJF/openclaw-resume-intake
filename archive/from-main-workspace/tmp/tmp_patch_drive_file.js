from pathlib import Path

p = Path('/root/.openclaw/extensions/openclaw-lark/src/tools/oapi/drive/file.js')
text = p.read_text(encoding='utf-8')

old_schema = '''        parent_node: typebox_1.Type.Optional(typebox_1.Type.String({
            description: '父节点 token（可选）。explorer 类型填文件夹 token，bitable 类型填 app_token。不填写或填空字符串时，上传到云空间根目录',
        })),
'''
new_schema = '''        parent_type: typebox_1.Type.Optional(typebox_1.Type.Union([
            typebox_1.Type.Literal('explorer'),
            typebox_1.Type.Literal('bitable_file'),
        ], {
            description: '父节点类型（可选，默认 explorer）。上传为多维表格附件时使用 bitable_file。',
        })),
        parent_node: typebox_1.Type.Optional(typebox_1.Type.String({
            description: '父节点 token（可选）。explorer 类型填文件夹 token，bitable_file 类型填 app_token。不填写或填空字符串时，上传到云空间根目录',
        })),
'''
if old_schema not in text:
    raise SystemExit('schema block not found')
text = text.replace(old_schema, new_schema, 1)

text = text.replace("parent_type: 'explorer',", "parent_type: p.parent_type || 'explorer',")

needle = "                            log.info(`upload: file_token=${res.data?.file_token}`);\n                            return (0, helpers_1.json)({\n                                file_token: res.data?.file_token,\n                                file_name: fileName,\n                                size: fileSize,\n                            });"
if needle not in text:
    raise SystemExit('small upload return block not found')
text = text.replace(needle, "                            const fileToken = res.data?.file_token || res?.data?.token || res?.file_token;\n                            log.info(`upload: file_token=${fileToken}`);\n                            return (0, helpers_1.json)({\n                                success: true,\n                                file_token: fileToken,\n                                file_name: fileName,\n                                size: fileSize,\n                                parent_type: p.parent_type || 'explorer',\n                                parent_node: p.parent_node || '',\n                            });", 1)

needle2 = "                            log.info(`upload: file_token=${finishRes.data?.file_token}`);\n                            return (0, helpers_1.json)({\n                                file_token: finishRes.data?.file_token,\n                                file_name: fileName,"
if needle2 not in text:
    raise SystemExit('finish upload return block not found')
text = text.replace(needle2, "                            const fileToken = finishRes.data?.file_token || finishRes?.data?.token || finishRes?.file_token;\n                            log.info(`upload: file_token=${fileToken}`);\n                            return (0, helpers_1.json)({\n                                success: true,\n                                file_token: fileToken,\n                                file_name: fileName,", 1)

p.write_text(text, encoding='utf-8')
print('PATCHED_OK')
