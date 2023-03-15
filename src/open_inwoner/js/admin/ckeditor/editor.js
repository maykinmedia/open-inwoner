import ClassicEditorBase from '@ckeditor/ckeditor5-editor-classic/src/classiceditor'
import Essentials from '@ckeditor/ckeditor5-essentials/src/essentials'
import Paragraph from '@ckeditor/ckeditor5-paragraph/src/paragraph'
import Bold from '@ckeditor/ckeditor5-basic-styles/src/bold'
import Italic from '@ckeditor/ckeditor5-basic-styles/src/italic'
import Autoformat from '@ckeditor/ckeditor5-autoformat/src/autoformat'
import BlockQuote from '@ckeditor/ckeditor5-block-quote/src/blockquote'
import Heading from '@ckeditor/ckeditor5-heading/src/heading'
import Indent from '@ckeditor/ckeditor5-indent/src/indent'
import Link from '@ckeditor/ckeditor5-link/src/link'
import List from '@ckeditor/ckeditor5-list/src/list'
import Markdown from '@ckeditor/ckeditor5-markdown-gfm/src/markdown'
import Image from '@ckeditor/ckeditor5-image/src/image'
import ImageUpload from '@ckeditor/ckeditor5-image/src/imageupload'
import ImageStyle from '@ckeditor/ckeditor5-image/src/imagestyle'
import ImageToolbar from '@ckeditor/ckeditor5-image/src/imagetoolbar'
import ImageCaption from '@ckeditor/ckeditor5-image/src/imagecaption'
import Table from '@ckeditor/ckeditor5-table/src/table'
import TableToolbar from '@ckeditor/ckeditor5-table/src/tabletoolbar'
import FilerImageAdapterPlugin from './plugins/filer/plugin'

import Plugin from '@ckeditor/ckeditor5-core/src/plugin'
import ButtonView from '@ckeditor/ckeditor5-ui/src/button/buttonview'

export default class ClassicEditor extends ClassicEditorBase {}

class CTARequestButtonPlugin extends Plugin {
  init() {
    const editor = this.editor

    editor.ui.componentFactory.add('addRequest', () => {
      // The button will be an instance of ButtonView.
      const button = new ButtonView()

      button.set({
        label: 'Add request button',
        withText: true,
      })

      //Execute a callback function when the button is clicked
      button.on('execute', () => {
        const formId = document.getElementById('id_form')
        const linkId = document.getElementById('id_link')
        let productSlug = ''

        if (formId) {
          productSlug = formId.dataset.productSlug
        } else if (linkId) {
          productSlug = linkId.dataset.productSlug
        }

        editor.model.change((writer) => {
          const link = writer.createText(`[CTA/${productSlug}]`)

          editor.model.insertContent(link, editor.model.document.selection)
        })
      })

      return button
    })
  }
}

// Plugins to include in the build.
ClassicEditor.builtinPlugins = [
  Markdown,
  Essentials,
  Paragraph,
  Bold,
  Italic,
  Autoformat,
  BlockQuote,
  Heading,
  Indent,
  Link,
  List,
  Image,
  ImageUpload,
  ImageToolbar,
  ImageCaption,
  ImageStyle,
  FilerImageAdapterPlugin,
  Table,
  TableToolbar,
  CTARequestButtonPlugin,
]

// Editor configuration.
ClassicEditor.defaultConfig = {
  toolbar: {
    items: [
      'heading',
      '|',
      'bold',
      'italic',
      'link',
      'blockQuote',
      '|',
      'bulletedList',
      'numberedList',
      '|',
      'outdent',
      'indent',
      '|',
      'uploadImage',
      'insertTable',
      '|',
      'undo',
      'redo',
      '|',
      'addRequest',
    ],
  },
  image: {
    toolbar: [
      'imageStyle:inline',
      'imageStyle:block',
      'imageStyle:side',
      '|',
      'toggleImageCaption',
      'imageTextAlternative',
    ],
    upload: {
      types: ['jpeg', 'png', 'gif'],
    },
  },
  table: {
    contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells'],
  },
}

export const getEditor = (node) => {
  ClassicEditor.create(node)
    .then((editor) => {
      console.log('Editor was initialized', editor)
    })
    .catch((error) => {
      console.log(error)
      console.error(error.stack)
    })
}
