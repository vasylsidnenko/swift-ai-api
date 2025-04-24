// Highlights fields with values by adding .has-value
function updateFieldHighlight(field) {
  if (field.value && field.value.trim() !== "") {
    field.classList.add("has-value");
  } else {
    field.classList.remove("has-value");
  }
}

document.addEventListener("DOMContentLoaded", function() {
  const highlightFields = [
    document.getElementById("keywords"),
    document.getElementById("questionContext"),
    document.getElementById("tech"),
    document.getElementById("topic")
  ];
  highlightFields.forEach(function(field) {
    if (!field) return;
    updateFieldHighlight(field);
    field.addEventListener("input", function() {
      updateFieldHighlight(field);
    });
  });
});
