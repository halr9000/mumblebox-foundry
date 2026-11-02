module.exports = {
  requires: {bundle: "ai"},
  run: [
    {method:"shell.run",when:"{{!exists('.pinokio/launcher-env/Scripts/python.exe')}}",params:{message:"uv venv --seed --python 3.13.12 .pinokio/launcher-env"}},
    {method:"shell.run",params:{venv:".pinokio/launcher-env",message:"python scripts/pinokio/bootstrap.py --root .",on:[
      {event:"/Installation stopped:/",break:true},
      {event:"/Foundry software is installed[.]/",done:true}
    ]}}
  ]
};
