function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.cookie.split('; ')
               .find(row => row.startsWith('csrftoken='))
               ?.split('=')[1];
}

async function handleLike(element) {
    const id = element.dataset.id;
    const type = element.dataset.type;  
    const action = element.dataset.action; 
    
    const url = type === 'question' 
        ? '/ajax/like-question/' 
        : '/ajax/like-answer/';
    
    const formData = new FormData();
    formData.append(type + '_id', id);
    formData.append('action', action);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
            body: formData,
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        const counterId = type === 'question' 
            ? `question-likes-${id}` 
            : `answer-likes-${id}`;
        document.getElementById(counterId).textContent = data.likes_count;
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

async function handleCorrectAnswer(answerId) {
    const formData = new FormData();
    formData.append('answer_id', answerId);
    
    try {
        const response = await fetch('/ajax/correct-answer/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
            body: formData,
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        location.reload();
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', () => handleLike(btn));
    });
    
    document.querySelectorAll('.correct-btn').forEach(btn => {
        btn.addEventListener('click', () => handleCorrectAnswer(btn.dataset.answerId));
    });
// });

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tag').forEach(tag => {
        const hue = Math.floor(Math.random() * 360);
        // tag.style.backgroundColor = `hsl(${hue}, 70%, 85%)`;
        tag.style.color = `hsl(${hue}, 80%, 35%)`;
    });
});