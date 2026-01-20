import { Meta, StoryObj } from '@storybook/preact';
import OipCard, {
  Card,
  CardBody,
  CardHeading,
  LocationCard,
  LocationCardProps,
  OipCardProps,
} from './Card';

const meta: Meta = {
  title: 'Components/Card',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A reusable Card component system for displaying various types of content.

**Web Component:** \`<oip-card>\`

**Base Components:**
- \`Card\`: The main wrapper component with optional href and variant
- \`CardBody\`: Container for card content with padding
- \`CardHeading\`: Heading component with optional link
- \`CardContent\`: Flexible content container

**Specialized Cards:**
- \`LocationCard\`: Pre-built card for displaying location information

**Variants:**
- \`default\`: Standard card styling
- \`location\`: Optimized for contact/location information
- \`category\`: Optimized for category listings
- \`product\`: Optimized for product displays

**Web Component Usage:**
\`\`\`html
<!-- Default card -->
<oip-card
  title="Card Title"
  description="Card description text"
  href="/link"
></oip-card>

<!-- Card with badge and footer -->
<oip-card
  title="Parkeervergunning"
  description="ZB65 Oost-3a"
  href="/aanvraag/123"
  badge-label="Nieuw"
  badge-variant="success"
  footer="Aanvraagdatum: 10 juni 2025"
></oip-card>

<!-- Location card -->
<oip-card
  variant="location"
  location-name="Stadhuis"
  location-url="/locatie/stadhuis"
  address-line-1="Straatnaam 1"
  address-line-2="1000 AA Utrecht"
  phone-number="06 12345678"
  email="gemeente@utrecht.nl"
></oip-card>
\`\`\`
`,
      },
    },
  },
};
export default meta;

// LocationCard Stories
type LocationCardStory = StoryObj<LocationCardProps>;

const mockLocationData: LocationCardProps = {
  locationName: 'Stadhuis',
  locationUrl: 'https://localhost:8000/locatie/stadhuis',
  addressLine1: 'Straatnaam 1',
  addressLine2: '1000 AA Utrecht',
  phoneNumber: '06 12345678',
  email: 'gemeente@utrecht.nl',
};

export const Location: LocationCardStory = {
  name: 'LocationCard',
  render: (args) => <LocationCard {...args} />,
  args: mockLocationData,
  parameters: {
    docs: {
      description: {
        story:
          'LocationCard displaying contact information with clickable phone and email links.',
      },
    },
  },
};

export const LocationMinimal: LocationCardStory = {
  name: 'LocationCard - Minimal',
  render: (args) => <LocationCard {...args} />,
  args: {
    locationName: 'Gemeentehuis',
    locationUrl: 'https://localhost:8000/locatie/gemeentehuis',
    addressLine1: 'Hoofdstraat 100',
    addressLine2: '2000 BB Amsterdam',
  },
  parameters: {
    docs: {
      description: {
        story:
          'LocationCard with only address information, no contact details.',
      },
    },
  },
};

export const LocationWithoutUrl: LocationCardStory = {
  name: 'LocationCard - Without URL',
  render: (args) => <LocationCard {...args} />,
  args: {
    locationName: 'Bibliotheek',
    addressLine1: 'Leesplein 5',
    addressLine2: '3000 CC Rotterdam',
    email: 'info@bibliotheek.nl',
  },
  parameters: {
    docs: {
      description: {
        story: 'LocationCard without a link on the heading.',
      },
    },
  },
};

// Base Card Stories
export const BaseCard: StoryObj = {
  name: 'Base Card',
  render: () => (
    <Card>
      <CardBody>
        <CardHeading>Card Title</CardHeading>
        <p class="utrecht-paragraph">This is a basic card with some content.</p>
      </CardBody>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Basic card using the composable components.',
      },
    },
  },
};

export const LinkedCard: StoryObj = {
  name: 'Linked Card',
  render: () => (
    <Card href="https://example.com">
      <CardBody>
        <CardHeading>Clickable Card</CardHeading>
        <p class="utrecht-paragraph">The entire card is clickable.</p>
      </CardBody>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Card that acts as a link - the entire card surface is clickable.',
      },
    },
  },
};

export const CardWithLinkedHeading: StoryObj = {
  name: 'Card with Linked Heading',
  render: () => (
    <Card>
      <CardBody>
        <CardHeading href="https://example.com">Only Heading Links</CardHeading>
        <p class="utrecht-paragraph">
          Only the heading is clickable, not the entire card.
        </p>
      </CardBody>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card where only the heading is a link.',
      },
    },
  },
};

// OipCard Web Component Stories
type OipCardStory = StoryObj<OipCardProps>;

export const WebComponentDefault: OipCardStory = {
  name: 'Web Component - Default',
  render: (args) => <OipCard {...args} />,
  args: {
    title: 'Card Title',
    description: 'This is a description for the card.',
    href: 'https://example.com',
  },
  parameters: {
    docs: {
      description: {
        story:
          'OipCard web component with default variant. Usage: `<oip-card title="Card Title" description="..." href="...">`.',
      },
    },
  },
};

export const WebComponentLocation: OipCardStory = {
  name: 'Web Component - Location',
  render: (args) => <OipCard {...args} />,
  args: {
    variant: 'location',
    locationName: 'Stadhuis',
    locationUrl: 'https://localhost:8000/locatie/stadhuis',
    addressLine1: 'Straatnaam 1',
    addressLine2: '1000 AA Utrecht',
    phoneNumber: '06 12345678',
    email: 'gemeente@utrecht.nl',
  },
  parameters: {
    docs: {
      description: {
        story:
          'OipCard web component with variant="location". Usage: `<oip-card variant="location" location-name="..." ...>`.',
      },
    },
  },
};

export const WebComponentWithBadge: OipCardStory = {
  name: 'Web Component - With Badge',
  render: (args) => <OipCard {...args} />,
  args: {
    title: 'Parkeervergunning',
    // description: 'ZB65 Oost-3a\nStatus: in aanvraag',
    subtitle: 'OMG-2024-789',
    status: 'Status: in behandeling',
    href: '/aanvraag/123',
    badgeLabel: 'Nieuw',
    badgeVariant: 'success',
    footer: 'Aanvraagdatum: 10 juni 2025',
  },
  parameters: {
    docs: {
      description: {
        story:
          'OipCard with badge and footer. Usage: `<oip-card title="..." badge-label="Nieuw" badge-variant="success" footer="...">`.',
      },
    },
  },
};
