// // JavaScript code for handling file selection and removal
// const fileInput = document.getElementById("id_file");
// const fileList = document.getElementById("fileList");
// const maxBytes = Number(fileInput.dataset.maxSize);
// let selectedFiles = [];
//
// fileInput.addEventListener("change", handleFileSelect);
//
// function getFileExtension(fileName) {
//   // Split the file name by '.' and get the last part (the file extension)
//   const parts = fileName.split(".");
//   return parts[parts.length - 1];
// }
//
// function handleFileSelect(event) {
//   const files = Array.from(event.target.files);
//
//   // Clear the file list container and selectedFiles array
//   fileList.innerHTML = "";
//   selectedFiles = [];
//
//   files.forEach((file) => {
//     const fileDiv = document.createElement("div");
//     fileDiv.classList.add("file-item");
//
//     const fileHTML = `
//       <span class="file-material-icon">
//         <i class="material-icons assignment"></i>
//       </span>
//       <span class="file-name">${file.name}</span>
//       <span class="file-size">Size: ${file.size}</span>
//       <span class="file-extension">Extension: ${getFileExtension(
//         file.name
//       )}</span>
//       <button class="button button--textless button--icon button--icon-after button--transparent button-file-remove" type="button" title="Toegevoegd bestand verwijderen" aria-label="Toegevoegd bestand verwijderen">
//         <span class="material-icons"><i class="material-icons auto_delete"></i></span>
//         Delete
//       </button>
//     `;
//
//     fileDiv.innerHTML = fileHTML;
//
//     if (file.size > maxBytes) {
//       fileDiv.classList.add("error-message");
//       const fileSizeError = document.createElement("div");
//       fileSizeError.textContent = "Dit bestand is te groot";
//       fileSizeError.classList.add("error-message");
//       fileDiv.querySelector(".file-material-icon").appendChild(fileSizeError);
//     }
//
//     fileList.appendChild(fileDiv);
//     selectedFiles.push(file);
//   });
// }
//
// // Use event delegation to handle file removal
// fileList.addEventListener("click", (event) => {
//   if (event.target.classList.contains("button-file-remove")) {
//     const fileDiv = event.target.parentElement;
//     const index = selectedFiles.findIndex(
//       (file) => file.name === fileDiv.querySelector(".file-name").textContent
//     );
//
//     if (index !== -1) {
//       selectedFiles.splice(index, 1);
//     }
//
//     fileDiv.remove();
//     fileInput.value = "";
//   }
// });
//
// function submitForm() {
//   let content = "Selected Files:\n";
//   selectedFiles.forEach((file, index) => {
//     content += `${index + 1}. ${file.name} - Size: ${file.size} bytes\n`;
//   });
//   alert(content);
//
//   const formData = new FormData();
//   selectedFiles.forEach((file, index) => {
//     formData.append(`file${index + 1}`, file);
//   });
//   // Submit formData to the backend using AJAX or form submission
// }
