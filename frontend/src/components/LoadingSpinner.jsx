function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="min-h-screen bg-fantasy-dark flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-fantasy-purple border-t-transparent mb-4"></div>
        <p className="text-xl text-gray-300">{message}</p>
      </div>
    </div>
  );
}

export default LoadingSpinner;