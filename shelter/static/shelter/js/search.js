// Search functionality for pets page - Django Version
// Most filtering is handled server-side in Django views

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for pagination
    const paginationLinks = document.querySelectorAll('.pagination-btn');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });
});
