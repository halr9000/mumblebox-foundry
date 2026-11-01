// Shared presentation of the creator's saved usage permissions.
// These values describe the creator's flags; they do not replace base-model terms.
export function modelUsageRows(permissions={},includeUnknown=false) {
    const p=permissions&&typeof permissions==="object"?permissions:{};
    const flag=(key,yes,no)=>p[key]===true?yes:p[key]===false?no:"Not specified";
    const commercial=Array.isArray(p.allowCommercialUse)
        ?p.allowCommercialUse.filter(value=>typeof value==="string").join(", ")||"None listed by creator"
        :flag("allowCommercialUse","Allowed by creator","Restricted by creator");
    return [
        ["Commercial permissions",commercial],
        ["Credit",flag("allowNoCredit","Not required by creator","Required by creator")],
        ["Derived models",flag("allowDerivatives","Allowed by creator","Restricted by creator")],
        ["Different license",flag("allowDifferentLicense","Allowed by creator","Restricted by creator")],
    ].filter(([,value])=>includeUnknown||value!=="Not specified");
}
