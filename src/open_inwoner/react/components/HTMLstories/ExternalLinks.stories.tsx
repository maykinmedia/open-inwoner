import { Meta, StoryObj } from '@storybook/react'

const meta: Meta = {
  title: 'HTML/Components/ExternalLinks',
  parameters: {
    docs: {
      description: {
        component: `
The ExternalLinks 'Ga naar' plugin displays a tiled list of links to external portals.

This plug-in uses styling coming from \`openinwoner-theme\` NLDS design-tokens.

**Plugin properties:**
- \`link_plugin.title\`: The title displayed as a heading for the plugin block.
- \`link.get_link\`: The links that wraps the entire link-item.
- \`link.target\`: Link-target: whether the link should open a blank page or not.
- \`link.name.html\`: The rich-formatted text displayed for the link.
- \`link.icon\`: The large custom icon placed before the link-text.
`,
      },
    },
  },
}

export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <div
      dangerouslySetInnerHTML={{
        __html: `
<section class="plugin external-links">
  <h2 class="utrecht-heading-2">Ga naar</h2>
  <ul class="card-container card-container--columns-2 external-links__list">
    <li class="external-links__list-item">
      <a href="https://example.com" class="external-link" target="_blank">
        <span class="external-link__custom-icon">
          <span aria-hidden="true" class="material-icons-outlined">account_balance</span>
        </span>
        <span class="external-link__content"><p class="utrecht-heading-3">Mijn belastingen</p></span>
        <span class="external-link__arrow">
          <span aria-hidden="true" class="material-icons-outlined">east</span>
        </span>
      </a>
    </li>
    <li class="external-links__list-item">
      <a href="https://example.com" class="external-link" target="_blank">
        <span class="external-link__custom-icon">
          <span aria-hidden="true" class="material-icons-outlined">local_parking</span>
        </span>
        <span class="external-link__content"><p class="utrecht-heading-3">Mijn <em>parkeer</em> vergunning</p></span>
        <span class="external-link__arrow">
          <span aria-hidden="true" class="material-icons-outlined">east</span>
        </span>
      </a>
    </li>
    <li class="external-links__list-item">
      <a href="https://example.com" class="external-link" target="_blank">
        <span class="external-link__custom-icon">
          <span aria-hidden="true" class="material-icons-outlined">group</span>
        </span>
        <span class="external-link__content"><p class="utrecht-heading-3"><u>Amsterdam</u> 750 jaar</p></span>
        <span class="external-link__arrow">
          <span aria-hidden="true" class="material-icons-outlined">east</span>
        </span>
      </a>
    </li>
  </ul>
</section>
        `,
      }}
    />
  ),
}
