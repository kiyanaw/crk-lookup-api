import handler
import json

def test_bulk_lookup(mocker):
  mocker.patch('handler.get_transducer')

  # patch main lookup
  fst_response = {'êkwa': {'êkwa+Ipc'}, 'kiya': {'RdplW+_+Ind+2+Err/Frag', 'PV/kiyi+RdplW+_+Cnj+Err/Frag', 'PV/ki+RdplW+_+Cnj+Err/Frag', 'PV/ke+RdplW+_+Cnj+Err/Frag', 'PV/ki+RdplW+_+Ind+3+Err/Frag', 'kiya+Pron+Pers+2Sg+Err/Orth', 'kiya+Pron+Pers+2Sg'}, 'nikamow': {'nikamow+V+AI+Ind+3Sg+Err/Frag', 'nikamow+V+AI+Ind+3Sg'}, 'âhpo': {'ahpô+Ipc'}, 'foobar': set()}
  mocker.patch('handler.analyze_strict', return_value=fst_response)

  # patch suggestions
  first_response = {'foobar': {'fôbâr+Ipc'}}
  mocker.patch('handler.analyze_relaxed', return_value=first_response)
  second_response = {'fôbâr+Ipc': {'fôbâr'}}
  mocker.patch('handler.generate_strict', return_value=second_response)

  raw = handler.bulk_lookup({'body': '["foobar"]'}, {})
  response = json.loads(raw.get('body'))
  assert len(response['êkwa']) == 1
  assert len(response['kiya']) == 7
  assert len(response['foobar']) == 0

  # check for unknowns
  assert response['_suggestions']['foobar'] == 'fôbâr'


def test_suggest(mocker):
  mocker.patch('handler.get_transducer')
  # set up fst calls
  first_response = {'owāhkomākan': {'PV/o+wâhkômêw+V+TA+Imp+Del+2Sg+3SgO+Err/Orth'}, 'ekwa': {'êkwa+Ipc'}}
  mocker.patch('handler.analyze_relaxed', return_value=first_response)
  second_response = {'PV/o+wâhkômêw+V+TA+Imp+Del+2Sg+3SgO+Err/Orth': {'ôwâhkômâhkan'}, 'êkwa+Ipc': {'êkwa'}}
  mocker.patch('handler.generate_strict', return_value=second_response)
  # doit
  raw = handler.suggest({'body': '["owāhkomākan", "ekwa"]'}, {})

  response = json.loads(raw.get('body'))
  assert response['owāhkomākan'] == 'ôwâhkômâhkan'
  assert response['ekwa'] == 'êkwa'