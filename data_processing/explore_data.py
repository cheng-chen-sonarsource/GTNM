#%%
import json
import os
import pickle

body_pkl = "data-small/raw/saved/test_body.pkl"
pro_pkl = "data-small/raw/saved/test_pro.pkl"
tag_pkl = "data-small/raw/saved/test_tag.pkl"
doc_w2id = "data_processing/sub_token_w2id.txt"

assert os.path.isfile(body_pkl)
assert os.path.isfile(pro_pkl)
assert os.path.isfile(tag_pkl)
assert os.path.isfile(doc_w2id)

with open(body_pkl, "rb") as fid:
    body = pickle.load(fid)

with open(pro_pkl, "rb") as fid:
    pro = pickle.load(fid)

with open(tag_pkl, "rb") as fid:
    tag = pickle.load(fid)

with open(doc_w2id, "r") as fid:
    w2id = json.load(fid)

id2w = {item[1]:item[0] for item in w2id.items()}

#%%

index = 1
print("tag:" + " ".join([id2w[token] for token in tag[index]]))
print("body:" + " ".join([id2w[token] for token in body[index]]))
print("pro:" + " ".join([id2w[token] for token in pro[index]]))