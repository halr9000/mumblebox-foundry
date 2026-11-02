const path = require('path');
const start = path.resolve(__dirname, 'start.js');
module.exports = {
  requires:{bundle:"ai"},
  run:[
    {method:"shell.run",params:{venv:".pinokio/envs/host",message:"python scripts/pinokio/maintenance.py check-idle --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}},
    {method:"shell.run",params:{venv:".pinokio/envs/host",message:"python scripts/pinokio/maintenance.py stop-owned --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}},
    {method:"script.stop",params:{uri:start}},
    {method:"shell.run",params:{venv:".pinokio/envs/host",message:"python scripts/pinokio/maintenance.py update --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}},
    {method:"script.start",params:{uri:start}}
  ]
};
