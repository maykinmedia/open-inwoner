const searchForm = document.getElementById("search_form")
const feedbackThumbsup = document.getElementById("thumbsup")
const feedbackThumbsdown = document.getElementById("thumbsdown")
const feedbackRemark = document.getElementById("id_remark")
const feedbackVersturen = document.getElementById("feedback_versturen")
feedbackThumbsup.style.display = "none";
feedbackThumbsdown.style.display = "none";
feedbackRemark.style.display = "none";
feedbackVersturen.style.display = "none";

searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    feedbackThumbsup.style.display = ""
    feedbackThumbsdown.style.display = ""
    feedbackRemark.style.display = ""
    feedbackVersturen.style.display = ""

});