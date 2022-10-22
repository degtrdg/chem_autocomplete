from flask_cors import CORS
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from rdkit import Chem
from flask import Flask, jsonify, request
from flask import send_file
from rdkit import RDLogger  
from rdkit.Chem.Draw import IPythonConsole # may be needed for viewing of molecules in notebook
RDLogger.DisableLog('rdApp.*') 
from io import BytesIO
import base64



app = Flask(__name__)
CORS(app)

@app.route('/predict', methods=['POST'])
def predict_sentiment():
    data = request.get_json()
    sentences = prediction(data['sentence'])

    b = BytesIO(Chem.Draw.MolsToGridImage(
          [Chem.MolFromSmiles(x) for x in sentences]
      ).data)

    b.seek(0)
    img = base64.b64encode(b.read()).decode('utf-8')

    return jsonify({'image': img})

def smi_tokenizer(smi):
    """
    Tokenize a SMILES molecule or reaction
    """
    import re
    pattern =  "(\[[^\]]+]|Br?|Cl?|N|O|S|P|F|I|b|c|n|o|s|p|\(|\)|\.|=|#|-|\+|\\\\|\/|:|~|@|\?|>|\*|\$|\%[0-9]{2}|[0-9])"
    regex = re.compile(pattern)
    tokens = [token for token in regex.findall(smi)]
    return tokens

def prediction(original):
  counter = 0
  # BFS search for the shortest SMILE
  final = set()
  while len(final) < 15 and counter < 5000:
    input_seq = smi_tokenizer(original)
    input_seq = [unique_tokens.index(i) for i in input_seq]
    input_seq_ex_last = [54] + input_seq[:-1] if len(input_seq) != 0 else [54] # start with space to show that it is a new sequence
    input_seq_ex_last = torch.tensor(input_seq_ex_last) 
    input_seq_ex_last = torch.unsqueeze(input_seq_ex_last, dim=1)
    input_seq = torch.tensor([input_seq[-1]])
    input_seq = torch.unsqueeze(input_seq, dim=1)
    hidden_state = None
    min_pred_len = 5
    curr_final = set()

    #Create hidden state with n - 1 of the input
    if len(input_seq_ex_last) != 1:
      output, hidden_state = rnn_copy(input_seq_ex_last, hidden_state)

    queue = [(original, input_seq, hidden_state)]
    data_ptr = 0

    while True:
        # forward pass
        curr_output, input_seq, hidden_state = queue[0]
        output, hidden_state = rnn_copy(input_seq, hidden_state)

        # Do a BFS to find the shortest path to the end of the sequence 
        curr_len = len(queue)
        output = F.softmax(torch.squeeze(output), dim=0)

        # Pick three characters from the probability distribution
        dist = Categorical(output)
        ids = set()
        while len(ids) < 2:
          ids.add(dist.sample().item())

        print_top3 = [unique_tokens[i] for i in ids]
        for top, id in zip(print_top3, ids):
          counter += 1
          if (top == " " or data_ptr > min_pred_len) and Chem.MolFromSmiles(curr_output + top) != None:
            final.add(curr_output + top)
          elif top != ' ':
            # Curr path, next input, next hidden state
            queue.append((curr_output + top, torch.tensor([[id]]), hidden_state))

        # Remove old paths
        queue = queue[curr_len:]

        data_ptr += 1
  
        if data_ptr > op_seq_len or len(curr_final) > 4 or len(queue) == 0:
            final = final.union(curr_final)
            break

  final = sorted(final, key=lambda x: len(x))
  return final[:5] 

@app.route('/', methods=['GET'])
def hello():
    return jsonify({"response":"This is Sentiment Application"})

class RNN(nn.Module):
    def __init__(self, input_size, output_size, hidden_size, num_layers):
        super(RNN, self).__init__()
        self.embedding = nn.Embedding(input_size, input_size)
        self.rnn = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers)
        self.decoder = nn.Linear(hidden_size, output_size)
    
    def forward(self, input_seq, hidden_state):
        embedding = self.embedding(input_seq)
        output, hidden_state = self.rnn(embedding, hidden_state)
        output = self.decoder(output)
        return output, (hidden_state[0].detach(), hidden_state[1].detach())

@app.before_first_request
def before_first_request():
    print("Loading model...")
    global unique_tokens, hidden_size, seq_len, num_layers, rnn_copy, op_seq_len
    unique_tokens = ['#','(',')','-','.','/','1','2','3','4','5','6','=','B','Br','C','Cl','F','I','N','O','P','S','[135I]','[2H]','[Br-]','[C@@H]','[C@@]','[C@H]','[C@]','[Cl-]','[I-]','[Li+]','[N+]','[N-]','[Na+]','[O-]','[OH-]','[PH]','[S+]','[S-]','[S@@+]','[Se]','[Si]','[n+]','[n-]','[nH]','[o+]','[s+]','\\','c','n','o','s',' ']
    hidden_size = 512   # size of hidden state
    seq_len = 100       # length of LSTM sequence
    num_layers = 3      # num of layers in LSTM layer stack
    op_seq_len = 50     # total num of characters in output test sequence

    # model instance
    rnn_copy = RNN(len(unique_tokens), len(unique_tokens), hidden_size, num_layers)

    # trained on GPU from Colab but loaded on local CPU
    rnn_copy.load_state_dict(torch.load("./rnn.pth", map_location=torch.device('cpu')))


if __name__ == '__main__':
    app.run(host="0.0.0.0", threaded=True, port=5000)