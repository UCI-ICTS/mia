// src/components/CheckBoxForm.js

import React from "react";

const CheckboxForm = ({ nodeId, invite_id, onSubmit }) => {
    const [formValues, setFormValues] = React.useState({});
  
    const handleChange = (e) => {
      const { name, checked } = e.target;
      setFormValues(prev => ({ ...prev, [name]: checked }));
    };
  
    const handleSubmit = (e) => {
      e.preventDefault();
      const selected = Object.entries(formValues).filter(([key, val]) => val);
      if (selected.length > 0 && onSubmit) {
        onSubmit(nodeId);  // this calls `handleResponseClick(nodeId)`
      }
    };
  
    return (
      <form onSubmit={handleSubmit} style={{ textAlign: "center", marginTop: 20 }}>
        <label style={{ marginRight: 10 }}>
          <input type="checkbox" name="myself" onChange={handleChange} /> Myself
        </label>
        <label style={{ marginRight: 10 }}>
          <input type="checkbox" name="myChild" onChange={handleChange} /> My child/children
        </label>
        <label style={{ marginRight: 10 }}>
          <input type="checkbox" name="childOtherParent" onChange={handleChange} /> My child’s other parent
        </label>
        <label style={{ marginRight: 10 }}>
          <input type="checkbox" name="adultFamilyMember" onChange={handleChange} /> Another adult family member
        </label>
        <br />
        <button type="submit" disabled={!Object.values(formValues).some(v => v)} style={{ marginTop: 16 }}>
          Submit
        </button>
      </form>
    );
  };

  export default CheckboxForm;
  