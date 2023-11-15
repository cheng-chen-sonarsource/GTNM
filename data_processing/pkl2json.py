import json
import sys
import pickle


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pkl2json <input-file>")
        exit(1)
    input_file = sys.argv[1]
    output_file = ".".join(input_file.split(".")[:-1]) + ".json"

    with open(input_file, "rb") as fid:
        data = pickle.load(fid)

    with open(output_file, "w") as fid:
        json.dump(data, fid, indent=2)
