function ErrorMessage({ error, onRetry }) {
  return (
    <div className="min-h-screen bg-fantasy-dark flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-red-900 bg-opacity-20 border-2 border-red-500 rounded-lg p-8 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-red-400 mb-4">Something Went Wrong</h2>
        <p className="text-gray-300 mb-6">
          {error?.message || 'An unexpected error occurred. Please try again.'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg transition"
          >
            🔄 Try Again
          </button>
        )}
      </div>
    </div>
  );
}

export default ErrorMessage;