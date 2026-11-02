module.exports = {
  requires:{bundle:"ai"},
  run:[{method:"shell.run",params:{venv:".pinokio/launcher-env",message:"python scripts/pinokio/maintenance.py repair --root .",on:[{event:"/Foundry maintenance stopped:/",break:true}]}}]
};
