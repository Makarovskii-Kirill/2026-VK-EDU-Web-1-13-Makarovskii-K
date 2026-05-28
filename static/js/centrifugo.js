document.addEventListener('DOMContentLoaded', () => {
    const questionId = document.querySelector('[data-question-id]')?.dataset.questionId;
    if (!questionId) {
        console.log('No question ID found');
        return;
    }
    console.log('Question ID:', questionId);
    
    fetch('/centrifugo/token/')
        .then(r => r.json())
        .then(data => {
            console.log('Token received:', data.token ? 'yes' : 'no');
            
            const centrifuge = new Centrifuge('ws://127.0.0.1:8001/connection/websocket', {
                token: data.token,
            });
            
            centrifuge.on('connected', () => {
                console.log('CONNECTED!');
            });
            
            const channel = `questions:question:${questionId}`;
            console.log('Subscribing to:', channel);
            
            const sub = centrifuge.newSubscription(channel);
            
            sub.on('subscribing', () => console.log('Subscribing...'));
            sub.on('subscribed', () => console.log('SUBSCRIBED to', channel));
            sub.on('publication', (ctx) => {
                console.log('NEW MESSAGE:', ctx.data);
                alert('Новый ответ: ' + ctx.data.content);
            });
            sub.on('error', (err) => console.error('Subscription error:', err));
            
            sub.subscribe();
            centrifuge.connect();
        })
        .catch(e => console.error('Fetch error:', e));
});