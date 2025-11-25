from flask import Flask, request
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import os
import numpy as np

app = Flask(__name__)


class BertRNNClassifier(nn.Module):
    def __init__(self, base_model="bert-base-uncased", rnn_type="lstm", hidden_size=256, dropout=0.1, num_classes=2):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model, cache_dir="./")

        # Chọn loại RNN
        input_dim = self.encoder.config.hidden_size
        if rnn_type == "rnn":
            self.rnn = nn.RNN(input_dim, hidden_size,
                              batch_first=True, bidirectional=False)
        elif rnn_type == "lstm":
            self.rnn = nn.LSTM(input_dim, hidden_size,
                               batch_first=True, bidirectional=False)
        elif rnn_type == "bilstm":
            self.rnn = nn.LSTM(input_dim, hidden_size,
                               batch_first=True, bidirectional=True)
        elif rnn_type == "gru":
            self.rnn = nn.GRU(input_dim, hidden_size,
                              batch_first=True, bidirectional=False)
        else:
            raise ValueError(f"❌ Unsupported rnn_type: {rnn_type}")

        out_dim = hidden_size * (2 if "bi" in rnn_type else 1)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(out_dim, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids,
                               attention_mask=attention_mask)
        seq_out = outputs.last_hidden_state
        rnn_out, _ = self.rnn(seq_out)
        pooled = torch.mean(rnn_out, dim=1)
        pooled = self.dropout(pooled)
        logits = self.classifier(pooled)
        return logits


def predict_proba(texts):
    all_probs = []
    for text in texts:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN
        )
        with torch.no_grad():
            logits = model(
                input_ids=inputs["input_ids"].to(device),
                attention_mask=inputs["attention_mask"].to(device)
            )
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        all_probs.append(probs)
    return np.array(all_probs)


MODEL_PATH = "./models/roberta_lstm"
MODEL_NAME = "roberta-base"
MAX_LEN = 256

print("Đang tải model từ:", MODEL_PATH)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = BertRNNClassifier(
    base_model="roberta-base", rnn_type="lstm"
).to(device)
model.load_state_dict(torch.load(os.path.join(
    MODEL_PATH, "pytorch_model.bin"), map_location=device))
model.to(device)
model.eval()


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "").strip()

    probs = predict_proba([text])[0]
    pred = int(probs.argmax())
    confidence = float(probs[pred])
    print(f"Text: {text}")
    print(f"Predicted class: {pred} with confidence {confidence:.4f}")

    return {
        "prediction": pred,
        "confidence": confidence
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=36000)