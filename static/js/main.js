// Make sure no 'questions' declaration here; it's passed from Flask

const form = document.getElementById('quizForm');

// Dynamically render questions
questions.forEach(q => {
    const div = document.createElement('div');
    div.className = 'question-block';
    div.innerHTML = `
        <img src="/${q.image_url}" width="400"><br>
        <label><input type="radio" name="q${q.id}" value="A"> A</label><br>
        <label><input type="radio" name="q${q.id}" value="B"> B</label><br>
        <label><input type="radio" name="q${q.id}" value="C"> C</label><br>
        <label><input type="radio" name="q${q.id}" value="D"> D</label><br>
    `;
    form.appendChild(div);
    form.appendChild(document.createElement('hr'));
});

// Submit button
document.getElementById('submitBtn').addEventListener('click', () => {
    let score = 0;
    questions.forEach(q => {
        const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
        if(selected && selected.value === q.answer) score++;
    });

    fetch('/submit_score', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({username: 'testuser', challenge_code: challenge_code, score: score})
    })
    .then(res => res.json())
    .then(data => {
        alert('Your Score: ' + score);
    });
});
