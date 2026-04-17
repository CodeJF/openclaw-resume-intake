from pathlib import Path

p = Path('/root/.openclaw/extensions/openclaw-lark/src/tools/oapi/drive/file.js')
text = p.read_text(encoding='utf-8')

text = text.replace(
'''                        // 根据文件大小选择上传方式
                        if (fileSize <= SMALL_FILE_THRESHOLD) {
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
''',
'''                        // 根据文件大小选择上传方式
                        const parentType = p.parent_type || 'explorer';
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
''', 1)

text = text.replace(
'''                            const prepareRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadPrepare({
                                data: {
                                    file_name: fileName,
                                    parent_type: p.parent_type || 'explorer',
                                    parent_node: p.parent_node || '',
                                    size: fileSize,
                                },
                            }, opts), { as: 'user' });
''',
'''                            const prepareRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
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
''', 1)

text = text.replace(
'''                                await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadPart({
                                    data: {
                                        upload_id: String(upload_id),
                                        seq: Number(seq),
                                        size: Number(chunkBuffer.length),
                                        file: chunkBuffer,
                                    },
                                }, opts), { as: 'user' });
''',
'''                                await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
                                    ? sdk.drive.v1.media.uploadPart({
                                        data: {
                                            upload_id: String(upload_id),
                                            seq: Number(seq),
                                            size: Number(chunkBuffer.length),
                                            file: chunkBuffer,
                                        },
                                    }, opts)
                                    : sdk.drive.file.uploadPart({
                                        data: {
                                            upload_id: String(upload_id),
                                            seq: Number(seq),
                                            size: Number(chunkBuffer.length),
                                            file: chunkBuffer,
                                        },
                                    }, opts), { as: 'user' });
''', 1)

text = text.replace(
'''                            const finishRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => sdk.drive.file.uploadFinish({
                                data: {
                                    upload_id,
                                    block_num,
                                },
                            }, opts), { as: 'user' });
''',
'''                            const finishRes = await client.invoke('feishu_drive_file.upload', (sdk, opts) => useMediaApi
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
''', 1)

if 'media.uploadAll' not in text or 'media.uploadPrepare' not in text:
    raise SystemExit('patch did not apply as expected')

p.write_text(text, encoding='utf-8')
print('PATCHED_OK')
