import handler
import json

def test_bulk_lookup(mocker):
  mocker.patch('handler.get_transducer')

  fst_response = {'êkwa': {'êkwa+Ipc'}, 'kiya': {'RdplW+_+Ind+2+Err/Frag', 'PV/kiyi+RdplW+_+Cnj+Err/Frag', 'PV/ki+RdplW+_+Cnj+Err/Frag', 'PV/ke+RdplW+_+Cnj+Err/Frag', 'PV/ki+RdplW+_+Ind+3+Err/Frag', 'kiya+Pron+Pers+2Sg+Err/Orth', 'kiya+Pron+Pers+2Sg'}, 'nikamow': {'nikamow+V+AI+Ind+3Sg+Err/Frag', 'nikamow+V+AI+Ind+3Sg'}, 'âhpo': {'ahpô+Ipc'}, 'foobar': set()}
  mocker.patch('handler.do_lookup', return_value=fst_response)

  raw = handler.bulk_lookup({'body': 'foobar'}, {})

  response = json.loads(raw.get('body'))
  assert len(response['êkwa']) == 1
  assert len(response['kiya']) == 7
  assert len(response['foobar']) == 0
