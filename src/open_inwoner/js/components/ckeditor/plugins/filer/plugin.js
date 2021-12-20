import FilerImageAdapter from './adapter'

export default function FilerImageAdapterPlugin(editor) {
  editor.plugins.get('FileRepository').createUploadAdapter = (loader) => {
    return new FilerImageAdapter(loader)
  }
}
