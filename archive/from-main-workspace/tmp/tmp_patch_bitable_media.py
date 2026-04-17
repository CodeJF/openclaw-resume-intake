from pathlib import Path

p = Path('/root/.openclaw/extensions/openclaw-lark/src/tools/oapi/drive/file.js')
text = p.read_text(encoding='utf-8')
old = '''                        if (fileSize <= SMALL_FILE_THRESHOLD) {
                            // 小文件：使用一次上传
                            log.info(`upload: using upload_all (file size ${fileSize} <= 15MB)`);
                            const res = await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadAll({
                                data: {
                                    file_name: fileName,
                                    parent_type: p.parent_type || 'explorer',
                                    parent_node: p.parent_node || '',
                                    size: fileSize,
                                    file: fileBuffer,
                                },
                            }, opts), { as: 'user' });
'''
new = '''                        const parentType = p.parent_type || 'explorer';
                        const useMediaApi = parentType === 'bitable_file' || parentType === 'bitable_image';
                        if (fileSize <= SMALL_FILE_THRESHOLD) {
                            // 小文件：使用一次上传
                            log.info(`upload: using ${useMediaApi ? 'media.uploadAll' : 'file.uploadAll'} (file size ${fileSize} <= 15MB, parent_type=${parentType})`);
                            const res = await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
                                ? sdk.drive.v1.media.uploadAll({
                                    data: {
                                        file_name: fileName,
                                        parent_type: parentType,
                                        parent_node: p.parent_node || '',
                                        size: fileSize,
                                        file: fileBuffer,
                                    },
                                }, opts)
                                : sdk.drive.file.uploadAll({
                                    data: {
                                        file_name: fileName,
                                        parent_type: parentType,
                                        parent_node: p.parent_node || '',
                                        size: fileSize,
                                        file: fileBuffer,
                                    },
                                }, opts), { as: 'user' });
'''
if old not in text:
    raise SystemExit('small upload block not found')
text = text.replace(old, new, 1)

old2 = '''                            const prepareRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadPrepare({
                                data: {
                                    file_name: fileName,
                                    parent_type: p.parent_type || 'explorer',
                                    parent_node: p.parent_node || '',
                                    size: fileSize,
                                },
                            }, opts), { as: 'user' });
'''
new2 = '''                            const prepareRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
                                ? sdk.drive.v1.media.uploadPrepare({
                                    data: {
                                        file_name: fileName,
                                        parent_type: parentType,
                                        parent_node: p.parent_node || '',
                                        size: fileSize,
                                    },
                                }, opts)
                                : sdk.drive.file.uploadPrepare({
                                    data: {
                                        file_name: fileName,
                                        parent_type: parentType,
                                        parent_node: p.parent_node || '',
                                        size: fileSize,
                                    },
                                }, opts), { as: 'user' });
'''
if old2 not in text:
    raise SystemExit('prepare block not found')
text = text.replace(old2, new2, 1)

old3 = '''                                await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadPart({
                                    data: {
                                        upload_id,
                                        seq,
                                        size: chunk.length,
                                        file: chunk,
                                    },
                                }, opts), { as: 'user' });
'''
new3 = '''                                await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
                                    ? sdk.drive.v1.media.uploadPart({
                                        data: {
                                            upload_id,
                                            seq,
                                            size: chunk.length,
                                            file: chunk,
                                        },
                                    }, opts)
                                    : sdk.drive.file.uploadPart({
                                        data: {
                                            upload_id,
                                            seq,
                                            size: chunk.length,
                                            file: chunk,
                                        },
                                    }, opts), { as: 'user' });
'''
if old3 not in text:
    raise SystemExit('uploadPart block not found')
text = text.replace(old3, new3, 1)

old4 = '''                            const finishRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadFinish({
                                data: {
                                    upload_id,
                                    block_num,
                                },
                            }, opts), { as: 'user' });
'''
new4 = '''                            const finishRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
                                ? sdk.drive.v1.media.uploadFinish({
                                    data: {
                                        upload_id,
                                        block_num,
                                    },
                                }, opts)
                                : sdk.drive.file.uploadFinish({
                                    data: {
                                        upload_id,
                                        block_num,
                                    },
                                }, opts), { as: 'user' });
'''
if old4 not in text:
    raise SystemExit('uploadFinish block not found')
text = text.replace(old4, new4, 1)

p.write_text(text, encoding='utf-8')
print('PATCHED_OK')
