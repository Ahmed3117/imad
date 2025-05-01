// Assignment Details JavaScript
$(document).ready(function() {
    // Save grade functionality
    $('.save-grade-btn').click(function() {
        const answerId = $(this).data('answer-id');
        const gradeInput = $(`.grade-input[data-answer-id="${answerId}"]`);
        const feedbackInput = $(`.feedback-input[data-answer-id="${answerId}"]`);
        const statusDiv = $(`#grade-status-${answerId}`);
        
        const grade = gradeInput.val();
        const feedback = feedbackInput.val();
        
        if (grade === '') {
            statusDiv.html('<div class="alert alert-danger p-2">Please enter a grade</div>');
            return;
        }
        
        statusDiv.html('<div class="alert alert-info p-2">Saving...</div>');
        
        $.ajax({
            url: gradeAnswerUrl.replace('0', answerId),
            type: 'POST',
            data: {
                'grade': grade,
                'feedback': feedback,
                'csrfmiddlewaretoken': csrfToken
            },
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    statusDiv.html('<div class="alert alert-success p-2">Grade saved!</div>');
                } else {
                    statusDiv.html(`<div class="alert alert-danger p-2">${response.error}</div>`);
                }
                
                setTimeout(function() {
                    statusDiv.fadeOut();
                }, 3000);
            },
            error: function(xhr) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    statusDiv.html(`<div class="alert alert-danger p-2">${response.error}</div>`);
                } catch {
                    statusDiv.html('<div class="alert alert-danger p-2">Error saving grade</div>');
                }
            }
        });
    });
    
    // Grade input validation
    $('.grade-input').on('change', function() {
        const maxGrade = parseInt(maxGradeValue);
        const value = parseInt($(this).val()) || 0;
        
        if (value > maxGrade) {
            $(this).val(maxGrade);
        } else if (value < 0) {
            $(this).val(0);
        }
    });
});