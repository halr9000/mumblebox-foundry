module.exports = {
  requires:{bundle:"ai"},
  run:[
    {method:"shell.run",params:{venv:".pinokio/envs/host",message:"python scripts/pinokio/maintenance.py check-idle --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}},
    {when:"{{running('start.js')}}",method:"script.stop",params:{uri:"start.js"}},
    {method:"shell.run",params:{venv:".pinokio/envs/host",message:"python scripts/pinokio/maintenance.py update --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}},
    {method:"script.start",params:{uri:"start.js"}}
  ]
};
