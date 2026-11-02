module.exports = {
  requires:{bundle:"ai"},
  run:[{method:"shell.run",params:{venv:".pinokio/envs/host",message:"python scripts/pinokio/maintenance.py update --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}}]
};
