import { beforeEach, describe, expect, it, vi } from 'vitest';
import KVKBranchSelectorModule from './KVKBranchSelectorModule';

// Mock the i18n module
vi.mock('@react/i18n/i18n', () => ({
  getIntlProviderProps: vi.fn().mockResolvedValue({
    locale: 'nl',
    messages: {},
  }),
}));

describe('KVKBranchSelectorModule', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('initializes without errors when elements are found', async () => {
    const div = document.createElement('div');
    div.setAttribute('data-react-module', 'kvkbranchselector'); // Changed from 'selectcombobox'
    div.setAttribute('data-id', 'test-combobox');

    const script = document.createElement('script');
    script.id = 'branch-data'; // Changed from className to id
    script.type = 'application/json';
    script.textContent = JSON.stringify({
      items: [{ id: '1', label: 'Branch 1' }],
      selected_id: '1',
    });

    div.appendChild(script);
    document.body.appendChild(div);

    await KVKBranchSelectorModule.init();

    // Wait for React to finish rendering
    await vi.waitFor(() => {
      expect(div.querySelector('input[role="combobox"]')).toBeTruthy();
    });
  });

  it('handles invalid JSON gracefully without crashing', async () => {
    const div = document.createElement('div');
    div.setAttribute('data-react-module', 'kvkbranchselector'); // Changed

    const script = document.createElement('script');
    script.id = 'branch-data'; // Changed from className to id
    script.type = 'application/json';
    script.textContent = '{ invalid';

    div.appendChild(script);
    document.body.appendChild(div);

    await KVKBranchSelectorModule.init();
    await new Promise((resolve) => setTimeout(resolve, 100));
  });

  it('handles missing script tag gracefully', async () => {
    const div = document.createElement('div');
    div.setAttribute('data-react-module', 'kvkbranchselector'); // Changed

    document.body.appendChild(div);

    await KVKBranchSelectorModule.init();
    await new Promise((resolve) => setTimeout(resolve, 100));
  });
});
