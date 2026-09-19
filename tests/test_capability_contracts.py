from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_capability_contracts_cover_manifest_without_mixing_schemes():
    manifest = yaml.safe_load((ROOT / 'urisysnode/manifest.yaml').read_text())
    expected = {r['pattern']: r for r in manifest['uri_patterns']}
    seen = {}
    for filename in ['urisys-node.capabilities.markpact.md', 'urisys-node.app-capabilities.markpact.md']:
        text = (ROOT / 'markpacts' / filename).read_text()
        contract = yaml.safe_load(text.split('```yaml markpact:contract\n')[1].split('```')[0])
        for section in ['queries', 'commands']:
            for route in contract[section]:
                pattern = route['pattern']
                assert pattern.startswith(contract['scheme'] + '://')
                assert pattern not in seen
                assert route['id'] == expected[pattern]['operation']
                if section == 'commands':
                    assert route['requires_approval'] == (expected[pattern].get('approval', 'required') == 'required')
                    assert route['side_effects'] == expected[pattern].get('side_effects', True)
                seen[pattern] = route
    assert seen.keys() == expected.keys()
