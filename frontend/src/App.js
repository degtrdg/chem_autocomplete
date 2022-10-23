import React, { useState } from "react";
import "./App.css";
import { Input } from "semantic-ui-react";
import axios from "axios";

function App() {
  const [value, setValue] = useState("");
  const [output, setOutput] = useState("");
  const [errors, setErrors] = useState(false);

  const handleClick = () => {
    if (value !== "") {
      axios
        .post("https://chem-autocomplete.herokuapp.com/prediction", {
          sentence: value,
        })
        .then((response) => {
          setOutput(response.data["image"]);
        })
        .catch((err) => {
          console.log(err);
          setValue("");
          setOutput("");
          setErrors(true);
        });
    }
  };

  const handleValueChange = (e) => {
    if (errors) {
      setErrors(false);
    }
    if (e.target.value == "") {
      setOutput("");
      setErrors(false);
    }
    setValue(e.target.value);
  };

  const properSet = new Set(
    "#()-./123456=BBrCClFINOPS[135I][2H][Br-][C@@H][C@@][C@H][C@][Cl-][I-][Li+][N+][N-][Na+][O-][OH-][PH][S+][S-][S@@+][Se][Si][n+][n-][nH][o+][s+]\\cnos"
  );
  const properSetSize = properSet.size;

  return (
    // backgroundImage: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    <div
      style={{
        height: "100vh",
        width: "100vw",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        backgroundImage: "linear-gradient(135deg, #336666 0%, #9966FF 100%)",
        display: "table-cell",
        verticalAlign: "middle",
        horizontalAlign: "middle",
      }}
    >
      <div class="grid grid-cols-2 gap-4 p-10 h-screen">
        <div class="flex flex-col gap-10 pt-24 h-fit items-center justify-center">
          <div class="flex items-center justify-center">
            <Input
              value={value}
              transparent
              onChange={handleValueChange}
              action={{
                color: "blue",
                onClick: () => handleClick(),
                content: "Get prediction",
              }}
              placeholder="Try O..."
              style={{
                border: "1px solid #fff",
                padding: "10px",
                borderRadius: "5px",
              }}
            />
          </div>
          <div class="flex items-center justify-center">
            {value === "" ||
            new Set([...value, ...properSet]).size !== properSetSize ||
            output === "" ||
            errors ? (
              <div>
                <div>Please input valid SMILES to get prediction</div>
                {new Set([...value, ...properSet]).size !== properSetSize ? (
                  <div style={{ color: "red" }}>
                    (Invalid characters in SMILES)
                  </div>
                ) : (
                  ""
                )}
                {errors ? (
                  <div style={{ color: "red" }}>
                    (Invalid initial sequence for SMILES, please try again)
                  </div>
                ) : (
                  ""
                )}
              </div>
            ) : (
              <img src={"data:image/png;base64," + output}></img>
            )}
          </div>
        </div>
        <div class="bg-white">
          <div class="flex flex-col gap-10 pt-24 h-fit items-center justify-center">
            <div class="text-2xl font-bold">Small Molecule Autocomplete</div>
            <div class="p-10">
              This small molecule autocomplete takes in a incomplete SMILES
              (Simplified Molecular Input Line Entry System) string and outputs
              a valid SMILES molecule. This is done by using a RNN LSTM that
              enumerates the chemical space and outputs the most likely and
              smallest SMILES string.
            </div>
            <div>This is an example of how it can be used:</div>
            <img src={require("./ex_prediction.png")} class="w-1/2"></img>
          </div>
        </div>
      </div>
    </div>
  );
}

const styleLink = document.createElement("link");
styleLink.rel = "stylesheet";
styleLink.href =
  "https://cdn.jsdelivr.net/npm/semantic-ui/dist/semantic.min.css";
document.head.appendChild(styleLink);

export default App;
