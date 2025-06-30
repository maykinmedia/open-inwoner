import type { Meta } from '@storybook/react'

const meta: Meta = {
  title: 'Developer Docs', // sidebar link label
  parameters: {
    docs: {
      // Optional: remove Controls and Actions panels for pure doc page
      controls: { disable: true },
      actions: { disable: true },
      page: null, // We override page on Docs export story below
    },
  },
}

export default meta

// The single "Docs" story — this is what Storybook shows as the full doc page
export const Docs = {
  parameters: {
    docs: {
      page: () => (
        <div
          style={{
            maxWidth: 800,
            margin: '0 auto',
            padding: 20,
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          <h1>Developer Documentation</h1>
          <p style={{ fontSize: '1.1em', color: '#666', marginBottom: '2em' }}>
            This guide is a work in progress.
          </p>

          <h2>Introduction</h2>

          <h3>Introduction Open Inwoner development</h3>
          <p>
            A general overview of our different components and the frameworks in
            use.
          </p>

          <h4>React</h4>
          <p>Use when:</p>
          <ul>
            <li>interactive elements with a state rerender</li>
            <li>
              components that are not interactive yet do not exist as a
              webcomponent
            </li>
          </ul>

          <h4>Web components</h4>
          <p>Use when:</p>
          <ul>
            <li>an NLDS component is available</li>
          </ul>

          <h4>HTMX</h4>
          <p>Use HTMX:</p>
          <ul>
            <li>especially in forms with Django</li>
            <li>or simple interactive elements with database updates</li>
          </ul>

          <h4>HTML</h4>
          <p>Use when:</p>
          <ul>
            <li>above conditions do not apply</li>
            <li>the element is read only (simple tag)</li>
            <li>native HTML behaviour is preferred</li>
          </ul>

          <h2>Languages</h2>

          <h3>Typescript</h3>
          <p>Use when:</p>
          <ul>
            <li>external / imported components are used (strong typing)</li>
            <li>
              for new interactive components (such as React- and Web components)
            </li>
          </ul>

          <h3>Javascript</h3>
          <p>Use when:</p>
          <ul>
            <li>
              working on legacy code (code that is not yet converted to
              Typescript)
            </li>
            <li>component can not be converted to Typescript</li>
          </ul>

          <h3>CSS / SCSS</h3>
          <p>Use absolute imports.</p>

          <h2>Front-end development pipeline</h2>

          <h3>Vite</h3>
          <p>vite.config</p>
          <p>Potential future: Django-vite</p>

          <h3>ESlint</h3>

          <h3>Typescript</h3>
          <p>tsconfig</p>

          <h3>Storybook</h3>

          <h4>Chromatic</h4>

          <h3>Vitest</h3>

          <h3>CI check</h3>

          <h4>ESlint check</h4>

          <h4>Typescript check</h4>

          <h4>Vitest check</h4>

          <h3>Translations</h3>

          <h4>React-intl</h4>
          <pre
            style={{
              backgroundColor: '#f5f5f5',
              padding: '10px',
              borderRadius: '4px',
              overflow: 'auto',
            }}
          >
            <code>
              npm run makemessages{'\n'}
              ./bin/compilemessages.sh
            </code>
          </pre>

          <h4>Web components translation</h4>
          <p>To be expanded later.</p>
        </div>
      ),
    },
  },
}
