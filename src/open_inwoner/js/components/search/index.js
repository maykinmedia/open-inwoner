function showRemark() {
    document.querySelectorAll('#positive, #negative').forEach(element => {

        let feedbackRemark = document.querySelector('.remark');

        element.addEventListener('click', (e) => {
            e.stopPropagation();
            if (feedbackRemark.className.includes('show')) {
                feedbackRemark.classList.remove('show');
            }
            else {
                feedbackRemark.classList.add('show');
            }
        });
    });
}


function showFeedback() {

    let searchResults = document.querySelector('.search-results__list');

    if (searchResults) {
        document.querySelector('.feedback').classList.add('show');
        showRemark();
    }
};

showFeedback();
